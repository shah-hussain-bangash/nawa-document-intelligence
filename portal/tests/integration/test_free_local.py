from types import SimpleNamespace
import pytest,httpx
from fastapi import HTTPException
from uae_ai.core.config import Settings
from uae_ai.rag.retrieval import answer_question
from scripts.prepare_local_identity import prepare
from cryptography import x509


@pytest.mark.parametrize('url,env', [('http://remote.invalid/v1','local'),('http://127.0.0.1:11434/v1','production'),('http://user:secret@127.0.0.1/v1','local'),('http://127.0.0.1/admin','local')])
def test_local_model_does_not_weaken_external_route_policy(tmp_path,url,env):
    settings=Settings(app_env=env,auth_mode='oidc' if env=='production' else 'demo',seed_demo=False,web_origin='https://app.example' if env=='production' else 'http://localhost:5173',oidc_issuer='https://id.example',oidc_client='nawa',oidc_redirect='https://app.example/auth/callback',model_mode='ollama',model_name='qwen2.5:1.5b',model_url=url,data_dir=tmp_path)
    with pytest.raises(RuntimeError):settings.validate()


def test_ollama_uses_local_route_without_api_key_and_validates_citations(tmp_path,monkeypatch):
    settings=Settings(app_env='test',model_mode='ollama',model_name='qwen2.5:1.5b',data_dir=tmp_path)
    settings.validate();calls=[]
    real=httpx.Client
    def respond(request):
        calls.append(request)
        return httpx.Response(200,json={'choices':[{'message':{'content':'Two quotations are required [1].'}}]})
    def client(**options):
        assert options['trust_env'] is False
        return real(transport=httpx.MockTransport(respond),**options)
    monkeypatch.setattr('uae_ai.rag.retrieval.httpx.Client',client)
    doc=SimpleNamespace(id='doc',version=1,title='Policy',category='Policy',classification='synthetic',status='ready',pages=[{'page':1,'text':'Two procurement quotations are required.'}])
    result=answer_question('procurement quotations',[doc],settings)
    assert result['mode']=='ollama' and result['citations']
    assert str(calls[0].url)=='http://127.0.0.1:11434/v1/chat/completions'
    assert 'authorization' not in calls[0].headers


def test_local_identity_material_is_private_and_not_overwritten(tmp_path):
    target=prepare(tmp_path)
    cert=x509.load_pem_x509_certificate((target/'server.crt').read_bytes())
    assert 'localhost' in cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName)
    first=(target/'compose.env').read_bytes()
    assert len(first)>50
    with pytest.raises(RuntimeError):prepare(tmp_path)
    assert (target/'compose.env').read_bytes()==first
