class BTreeNode:
    def __init__(self, block_id, is_root=False):
        self.block_id = block_id
        self.parent_id = 0 if is_root else None  
        self.num_keys = 0
        self.keys = [0] * 19      
        self.values = [0] * 19    
        self.children = [0] * 20  
        
    def to_bytes(self):
        """Convert node to bytes for storage"""
        data = bytearray()
        data.extend(struct.pack('>Q', self.block_id))
        data.extend(struct.pack('>Q', self.parent_id if self.parent_id is not None else 0))
        data.extend(struct.pack('>Q', self.num_keys))
        for key in self.keys:
            data.extend(struct.pack('>Q', key))
        for value in self.values:
            data.extend(struct.pack('>Q', value))
        for child in self.children:
            data.extend(struct.pack('>Q', child))
        return data
    
    @classmethod
    def from_bytes(cls, data, block_id):
        """Create node from bytes from storage"""
        node = cls(block_id)
        
        offset = 8
        node.parent_id = struct.unpack('>Q', data[offset:offset+8])[0]
        offset += 8
        node.num_keys = struct.unpack('>Q', data[offset:offset+8])[0]
        offset += 8
        for i in range(19):
            node.keys[i] = struct.unpack('>Q', data[offset:offset+8])[0]
            offset += 8
        for i in range(19):
            node.values[i] = struct.unpack('>Q', data[offset:offset+8])[0]
            offset += 8
        for i in range(20):
            node.children[i] = struct.unpack('>Q', data[offset:offset+8])[0]
            offset += 8
        return node