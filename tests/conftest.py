from api.main import app, PrivacyAbstraction
from memory.memory_manager import MemoryManager

app.state.memory_manager = MemoryManager(db_path=":memory:")
app.state.privacy = PrivacyAbstraction()
