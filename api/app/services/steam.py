import logging

import httpx

logger = logging.getLogger(__name__)

_WORKSHOP_API = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"


async def resolve_workshop_map_name(workshop_id: str, fallback: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                _WORKSHOP_API,
                data={"itemcount": "1", "publishedfileids[0]": workshop_id},
            )
            resp.raise_for_status()
            details = resp.json()["response"]["publishedfiledetails"][0]
            title = details.get("title", "").strip()
            return title if title else fallback
    except Exception:
        logger.warning("Could not resolve Steam Workshop map name for id=%s", workshop_id)
        return fallback
