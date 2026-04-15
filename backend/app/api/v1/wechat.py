from fastapi import APIRouter
from pydantic import BaseModel
from urllib.parse import urlparse, urlunparse

from app.core.response import success
from app.services import wechat_service

router = APIRouter(prefix="/config", tags=["config"])


class ConfigReq(BaseModel):
    appid: str
    appsecret: str = ""
    proxy_url: str = ""


def _mask_proxy_credentials(proxy_url: str) -> str:
    """Mask any embedded credentials in a proxy URL: http://user:pass@host -> http://****:****@host."""
    if not proxy_url:
        return proxy_url
    try:
        parsed = urlparse(proxy_url)
        if parsed.username or parsed.password:
            masked = parsed._replace(
                netloc=f"****:****@{parsed.hostname}"
                + (f":{parsed.port}" if parsed.port else "")
            )
            return urlunparse(masked)
    except Exception:
        pass
    return proxy_url


@router.get("")
async def get_config():
    config = wechat_service.load_config()
    raw_proxy = config.get("proxy_url", "")
    masked = {
        "appid": config.get("appid", ""),
        "appsecret": "****" + config.get("appsecret", "")[-4:]
        if config.get("appsecret")
        else "",
        "configured": bool(config.get("appid") and config.get("appsecret")),
        "account_name": config.get("account_name", ""),
        "proxy_url": _mask_proxy_credentials(raw_proxy),
    }
    return success(masked)


@router.put("")
async def update_config(req: ConfigReq):
    wechat_service.save_config(req.appid, req.appsecret, req.proxy_url)
    return success(message="saved")


@router.post("/test")
async def test_connection(req: ConfigReq):
    """Save config and actually verify credentials against WeChat API."""
    wechat_service.save_config(req.appid, req.appsecret, req.proxy_url)
    token = wechat_service.get_access_token()
    return success({"valid": True, "account_name": "已配置公众号"})
