from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class NetworkNode:
    """Represents a single device on the network with its identified attributes."""
    ip: str
    mac: str
    discovery_method: str = "Unknown"
    hostname: str = "Unknown"
    vendor: str = "Unknown"
    role: str = "Unknown"
    services: List[str] = field(default_factory=list)
    confidence_score: int = 0  # 0-100 scale of how certain we are of the name

    def __str__(self):
        return f"[{self.ip}] {self.hostname} ({self.vendor}) - Role: {self.role}"
