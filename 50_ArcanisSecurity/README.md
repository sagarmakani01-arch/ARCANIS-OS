# ArcanisSecurity (50)

Capability-based security framework replacing the RBAC model. Fine-grained tokens with delegation, expiry, rate limiting, and audit logging.

```python
from arcanis_security import CapabilityManager, Capability
mgr = CapabilityManager()
token = mgr.grant(Capability.FILE_READ, "process-1", "/tmp/*")
mgr.authorize(token.token_id, "read", "/tmp/test.py")
```
