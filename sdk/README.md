# arche-sdk

Async Python client for the ARCHE behavioral-simulation and recommendation API.

```python
from sdk.client import ArcheClient

client = ArcheClient("http://127.0.0.1:8000")
health = await client.health()
```
