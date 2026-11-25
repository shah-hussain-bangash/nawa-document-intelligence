"""Generate local-only TLS material/admin config. No secret values are printed."""
from datetime import datetime,timedelta,timezone
import ipaddress
from pathlib import Path
import secrets
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import certifi
import json
from uuid import uuid4


def prepare(root):
    target=root/'.data/local-identity'
    target.mkdir(parents=True,exist_ok=True,mode=0o700)
    if any(target.iterdir()):
        raise RuntimeError('Local identity material already exists; refusing to overwrite keys or admin settings.')
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Nawa local development CA')])
    now=datetime.now(timezone.utc)
    ca=x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=365)).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True).sign(key,hashes.SHA256())
    server=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    certificate=x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'localhost')])).issuer_name(subject).public_key(server.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=90)).add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False).add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True).sign(key,hashes.SHA256())
    files={
      'server.key':server.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()),
      'server.crt':certificate.public_bytes(serialization.Encoding.PEM),
      'ca.pem':ca.public_bytes(serialization.Encoding.PEM),
      'trust-bundle.pem':Path(certifi.where()).read_bytes()+b'\n'+ca.public_bytes(serialization.Encoding.PEM),
      'compose.env':('LOCAL_IDENTITY_ADMIN_PASSWORD='+secrets.token_urlsafe(32)+'\n').encode(),
    }
    # Do not persist the CA signing key: rerun rotation explicitly with new material.
    for name,content in files.items():
        path=target/name
        with path.open('xb') as stream:stream.write(content)
        path.chmod(0o600 if name in {'server.key','compose.env'} else 0o644)
    return target


def validation_realm(target):
    """An isolated synthetic realm for validate_identity_login.py, never production."""
    if (target/'fixture.json').exists() or (target/'import').exists():
        raise RuntimeError('Refusing to overwrite identity validation fixtures')
    fixture={'subject':str(uuid4()),'username':'fixture-analyst','password':secrets.token_urlsafe(24)}
    realm={'realm':'nawa-validation','enabled':True,'sslRequired':'all','registrationAllowed':False,
        'clients':[{'clientId':'nawa-local-validation','enabled':True,'publicClient':True,'standardFlowEnabled':True,'directAccessGrantsEnabled':False,'redirectUris':['http://127.0.0.1:8137/auth/callback'],'attributes':{'pkce.code.challenge.method':'S256'}}],
        'users':[{'id':fixture['subject'],'username':fixture['username'],'enabled':True,'emailVerified':True,'firstName':'Synthetic','lastName':'Analyst','email':'fixture@example.invalid','credentials':[{'type':'password','value':fixture['password'],'temporary':False}]}]}
    (target/'import').mkdir(mode=0o700)
    for path,value in [(target/'fixture.json',fixture),(target/'import/nawa-validation.json',realm)]:
        with path.open('x',encoding='utf-8') as output:json.dump(value,output)
        path.chmod(0o600)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validation-realm',action='store_true',help='Generate a private synthetic realm for the opt-in live identity test')
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    path=prepare(args.root)
    if args.validation_realm:validation_realm(path)
    print('Prepared local TLS certificates and a private compose.env under .data/local-identity.')
    print('Read the free local services guide. Do not publish these files or paste their secret values.')
