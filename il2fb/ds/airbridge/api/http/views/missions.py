# coding: utf-8

import logging
import re

from stat import S_ISREG, S_ISDIR

from aiohttp.web import FileResponse

from il2fb.ds.airbridge.api.http.responses.rest import RESTBadRequest
from il2fb.ds.airbridge.api.http.responses.rest import RESTInternalServerError
from il2fb.ds.airbridge.api.http.responses.rest import RESTNotFound
from il2fb.ds.airbridge.api.http.responses.rest import RESTSuccess
from il2fb.ds.airbridge.api.http.security import with_authorization


LOG = logging.getLogger(__name__)


@with_authorization
async def browse_missions(request):
    pretty = 'pretty' in request.query
    root_dir = request.app['dedicated_server'].missions_dir

    try:
        relative_dir = request.match_info.get('dir_path', '')
        absolute_dir = (root_dir / relative_dir).resolve()
    except Exception:
        LOG.exception("HTTP failed to browse missions: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        dirs = []
        files = []

        result = {
            'dirs': dirs,
            'files': files
        }

        for node in absolute_dir.iterdir():
            st_mode = node.stat().st_mode

            if S_ISDIR(st_mode):
                dirs.append(node.name)
            elif (
                S_ISREG(st_mode) and
                node.suffix.lower() in {'.mis', '.properties'}
            ):
                files.append(node.name)

        dirs.sort()
        files.sort()

    except Exception:
        LOG.exception("HTTP failed to browse missions")
        return RESTInternalServerError(
            detail="failed to browse missions",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def get_mission(request):
    pretty = 'pretty' in request.query
    as_json = 'json' in request.query

    root_dir = request.app['dedicated_server'].missions_dir

    try:
        relative_path = request.match_info['file_path']
        absolute_path = (root_dir / relative_path)
    except Exception:
        LOG.exception("HTTP failed to get mission: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    if not absolute_path.exists():
        return RESTNotFound()

    if as_json:
        try:
            result = request.app['mission_parser'].parse(str(absolute_path))
        except Exception:
            LOG.exception(f"HTTP failed to parse mission `{absolute_path}`")
            return RESTInternalServerError(
                detail="failed to parse mission",
                pretty=pretty,
            )
        else:
            return RESTSuccess(payload=result, pretty=pretty)
    else:
        return FileResponse(absolute_path)


@with_authorization
async def upload_mission(request):
    pretty = 'pretty' in request.query
    root_dir = request.app['dedicated_server'].missions_dir

    try:
        relative_dir = request.match_info.get('dir_path', '')
        absolute_dir = (root_dir / relative_dir)
    except Exception:
        LOG.exception(
            "HTTP failed to upload mission: incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    if not absolute_dir.exists():
        absolute_dir.mkdir(parents=True, exist_ok=True)

    try:
        reader = await request.multipart()
    except Exception:
        LOG.exception("HTTP failed to upload mission: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        while True:
            part = await reader.next()
            if not part:
                break

            absolute_file = absolute_dir / part.filename

            if absolute_file.suffix.lower() not in {'.mis', '.properties'}:
                return RESTBadRequest(
                    detail="incorrect input data",
                    pretty=pretty,
                )

            # may rewrite existing file
            with open(absolute_file, 'wb') as f:
                while True:
                    chunk = await part.read_chunk()
                    if chunk:
                        f.write(chunk)
                    else:
                        break
    except Exception:
        LOG.exception("HTTP failed to upload mission")
        return RESTInternalServerError(
            detail="failed to upload mission",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


@with_authorization
async def delete_mission(request):
    pretty = 'pretty' in request.query
    root_dir = request.app['dedicated_server'].missions_dir

    try:
        relative_path = request.match_info['file_path']
        absolute_path = (root_dir / relative_path)
    except Exception:
        LOG.exception("HTTP failed to delete mission: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    if not absolute_path.exists():
        return RESTNotFound()

    try:
        absolute_path.unlink()

        properties_pattern = f"^{absolute_path.stem}(_\w{{2}})?.properties$"

        for node in absolute_path.parent.iterdir():
            if node.is_file() and re.match(properties_pattern, node.name):
                node.unlink()

    except Exception:
        LOG.exception("HTTP failed to delete mission")
        return RESTInternalServerError(
            detail="failed to delete mission",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


@with_authorization
async def load_mission(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    root_dir = request.app['dedicated_server'].missions_dir

    try:
        if timeout is not None:
            timeout = float(timeout)

        relative_path = request.match_info['file_path']
        absolute_path = (root_dir / relative_path)
    except Exception:
        LOG.exception("HTTP failed to load mission: incorrect input data")
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    if not absolute_path.exists():
        return RESTNotFound()

    try:
        await request.app['console_client'].load_mission(
            file_path=str(relative_path),
            timeout=timeout,
        )
    except Exception:
        LOG.exception("HTTP failed to load mission")
        return RESTInternalServerError(
            detail="failed to load mission",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


@with_authorization
async def get_current_mission_info(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to get current mission info: incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        result = await request.app['console_client'].get_mission_info(timeout)
    except Exception:
        LOG.exception("HTTP failed to get current mission info")
        return RESTInternalServerError(
            detail="failed to get current mission info",
            pretty=pretty,
        )
    else:
        return RESTSuccess(payload=result, pretty=pretty)


@with_authorization
async def begin_current_mission(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to begin current mission info: incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        await request.app['console_client'].begin_mission(timeout)
    except Exception:
        LOG.exception("HTTP failed to begin current mission")
        return RESTInternalServerError(
            detail="failed to begin current mission",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


@with_authorization
async def end_current_mission(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)
    except Exception:
        LOG.exception(
            "HTTP failed to end current mission info: incorrect input data"
        )
        return RESTBadRequest(
            detail="incorrect input data",
            pretty=pretty,
        )

    try:
        await request.app['console_client'].end_mission(timeout)
    except Exception:
        LOG.exception("HTTP failed to end current mission")
        return RESTInternalServerError(
            detail="failed to end current mission",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)


@with_authorization
async def unload_current_mission(request):
    pretty = 'pretty' in request.query
    timeout = request.query.get('timeout')

    try:
        if timeout is not None:
            timeout = float(timeout)

        await request.app['console_client'].unload_mission(timeout=timeout)
    except Exception:
        LOG.exception("HTTP failed to unload current mission")
        return RESTInternalServerError(
            detail="failed to unload current mission",
            pretty=pretty,
        )
    else:
        return RESTSuccess(pretty=pretty)
