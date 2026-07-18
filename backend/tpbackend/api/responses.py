from fastapi import HTTPException

# 4xx


def bad_request(msg="Bad request"):
    raise HTTPException(status_code=400, detail=msg)


def unauthorized(msg="Unauthorized"):
    raise HTTPException(status_code=401, detail=msg)


def forbidden(msg="Forbidden"):
    raise HTTPException(status_code=403, detail=msg)


def not_found(msg="Not found"):
    raise HTTPException(status_code=404, detail=msg)


# 5xx


def internal_server_error(msg="Internal server error"):
    raise HTTPException(status_code=500, detail=msg)


def service_unavailable(msg="Service unavailable"):
    raise HTTPException(status_code=503, detail=msg)
