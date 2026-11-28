"""Create a private synthetic Keycloak fixture for local development only.

Never prints credentials or overwrites an existing fixture directory. The
generated CA is trusted only by the test; it is not installed in Windows.
"""
import argparse
from datetime import datetime, timedelta, timezone
import ipaddress
import json
from pathlib import Path
import secrets
from uuid import uuid4
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID


def write_new(path, content):
    with path.open('xb') as output:
        output.write(content)


def prepare(target, *, phase=12):
    if phase not in (12, 13):
        raise ValueError('Only synthetic Phase 12 or Phase 13 fixtures are supported')
    realm_name = f'nawa-phase{phase}'
    web_port = 18765 if phase == 12 else 19765
    database = 'nawa_phase12' if phase == 12 else 'nawa_phase13_qa_demo'
    target.mkdir(parents=True, exist_ok=False)
    imports = target / 'import'
    imports.mkdir()
    now = datetime.now(timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'NAWA synthetic test CA')])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=30))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .sign(ca_key, hashes.SHA256()))
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')]))
              .issuer_name(ca_name).public_key(server_key.public_key()).serial_number(x509.random_serial_number())
              .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=14))
              .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),
                             x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False)
              .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
              .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
              .sign(ca_key, hashes.SHA256()))
    users = [{'subject': str(uuid4()), 'username': 'synthetic-' + role,
              'password': secrets.token_urlsafe(24), 'role': role} for role in ('analyst', 'reviewer', 'outsider')]
    redirect_uris = [f'http://127.0.0.1:{web_port}/auth/callback']
    if phase == 13:
        redirect_uris.append('http://127.0.0.1:19766/auth/callback')
    realm = {'realm': realm_name, 'enabled': True, 'sslRequired': 'all', 'registrationAllowed': False,
             'clients': [{'clientId': realm_name, 'enabled': True, 'publicClient': True,
                          'standardFlowEnabled': True, 'directAccessGrantsEnabled': False,
                          'redirectUris': redirect_uris,
                          'attributes': {'pkce.code.challenge.method': 'S256'}}],
             'users': [{'id': user['subject'], 'username': user['username'], 'enabled': True,
                        'firstName': 'Synthetic', 'lastName': user['role'].capitalize(),
                        'email': user['username'] + '@example.invalid', 'emailVerified': True,
                        'credentials': [{'type': 'password',
                        'value': user['password'], 'temporary': False}]} for user in users]}
    write_new(target / 'ca.pem', ca.public_bytes(serialization.Encoding.PEM))
    write_new(target / 'server.crt', server.public_bytes(serialization.Encoding.PEM))
    write_new(target / 'server.key', server_key.private_bytes(serialization.Encoding.PEM,
              serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    write_new(target / 'fixture.json', json.dumps({'users': users}).encode('utf-8'))
    write_new(imports / 'realm.json', json.dumps(realm).encode('utf-8'))
    write_new(target / 'db.env', ('POSTGRES_USER=nawa_test\nPOSTGRES_DB=' + database + '\nPOSTGRES_PASSWORD='
                                + secrets.token_urlsafe(32) + '\n').encode('utf-8'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phase', type=int, choices=(12, 13), default=12)
    args = parser.parse_args()
    prepare(args.output, phase=args.phase)
    print('Created an isolated synthetic identity fixture. No credentials were printed.')

