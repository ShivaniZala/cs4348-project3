import struct
import os

class BTreeNode:
    def __init__(self, block_id, is_root=False):
        self.block_id = block_id
        self.parent_id = 0 if is_root else None
        self.num_keys = 0
        self.keys = [0] * 19      
        self.values = [0] * 19    
        self.children = [0] * 20  
        
    def to_bytes(self):
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

class IndexFileManager:
    def __init__(self):
        self.current_file = None
        self.BLOCK_SIZE = 512
        self.MAGIC_NUMBER = b"4337PRJ3"
        self.cached_nodes = {}
        
    def read_header(self):
        with open(self.current_file, 'rb') as f:
            f.read(8)  
            root_id = struct.unpack('>Q', f.read(8))[0]
            next_block = struct.unpack('>Q', f.read(8))[0]
            return root_id, next_block
            
    def write_header(self, file, root_id=0, next_block=1):
        file.write(self.MAGIC_NUMBER)
        file.write(struct.pack('>Q', root_id))
        file.write(struct.pack('>Q', next_block))
        remaining_bytes = self.BLOCK_SIZE - 24
        file.write(b'\x00' * remaining_bytes)
        
    def read_node(self, block_id):
        if block_id == 0:
            return None
            
        if block_id in self.cached_nodes:
            return self.cached_nodes[block_id]
            
        with open(self.current_file, 'rb') as f:
            f.seek(block_id * self.BLOCK_SIZE)
            data = f.read(self.BLOCK_SIZE)
            node = BTreeNode.from_bytes(data, block_id)
            
        if len(self.cached_nodes) >= 3:
            self.cached_nodes.pop(next(iter(self.cached_nodes)))
        self.cached_nodes[block_id] = node
        return node
        
    def write_node(self, node):
        with open(self.current_file, 'r+b') as f:
            f.seek(node.block_id * self.BLOCK_SIZE)
            f.write(node.to_bytes())
        self.cached_nodes[node.block_id] = node

    def verify_header(self, file):
        magic = file.read(8)
        if magic != self.MAGIC_NUMBER:
            return False
        return True

    def create_file(self, filename):
        try:
            if os.path.exists(filename):
                response = input("File already exists. Overwrite? (y/n): ")
                if response.lower() != 'y':
                    print("Operation cancelled")
                    return
            
            with open(filename, 'wb') as f:
                self.write_header(f)
            self.current_file = filename
            print(f"Created new index file: {filename}")
        except Exception as e:
            print(f"Error creating file: {e}")
            
    def open_file(self, filename):
        try:
            with open(filename, 'rb') as f:
                if not self.verify_header(f):
                    print("Error: Invalid file format")
                    return
            self.current_file = filename
            print(f"Opened index file: {filename}")
        except FileNotFoundError:
            print("Error: File not found")
        except Exception as e:
            print(f"Error opening file: {e}")

    def get_next_block_id(self):
        _, next_block = self.read_header()
        with open(self.current_file, 'r+b') as f:
            f.seek(16)
            f.write(struct.pack('>Q', next_block + 1))
        return next_block

    def create_root_node(self, key, value):
        block_id = self.get_next_block_id()
        root = BTreeNode(block_id, is_root=True)
        root.keys[0] = key
        root.values[0] = value
        root.num_keys = 1
        self.write_node(root)
        
        with open(self.current_file, 'r+b') as f:
            f.seek(8)
            f.write(struct.pack('>Q', block_id))
        return root

    def _split_child(self, parent, index, child):
        new_node = BTreeNode(self.get_next_block_id())
        new_node.parent_id = parent.block_id
        
        mid = 9
        for i in range(mid + 1, 19):
            new_node.keys[i - (mid + 1)] = child.keys[i]
            new_node.values[i - (mid + 1)] = child.values[i]
            child.keys[i] = 0
            child.values[i] = 0
            
        if child.children[0] != 0:
            for i in range(mid + 1, 20):
                new_node.children[i - (mid + 1)] = child.children[i]
                child.children[i] = 0
        
        new_node.num_keys = 9
        child.num_keys = 9
        
        for i in range(parent.num_keys, index, -1):
            parent.keys[i] = parent.keys[i - 1]
            parent.values[i] = parent.values[i - 1]
            parent.children[i + 1] = parent.children[i]
            
        parent.keys[index] = child.keys[mid]
        parent.values[index] = child.values[mid]
        parent.children[index + 1] = new_node.block_id
        parent.num_keys += 1
        
        self.write_node(parent)
        self.write_node(child)
        self.write_node(new_node)

    def insert(self, key, value):
        root_id, _ = self.read_header()
        if root_id == 0:
            self.create_root_node(key, value)
            return True
            
        if self.search(key) is not None:
            return False
            
        current = self.read_node(root_id)
        return self._insert_non_full(current, key, value)

    def _insert_non_full(self, node, key, value):
        i = node.num_keys - 1
        
        if all(child == 0 for child in node.children):
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
                
            node.keys[i + 1] = key
            node.values[i + 1] = value
            node.num_keys += 1
            self.write_node(node)
            return True
            
        while i >= 0 and key < node.keys[i]:
            i -= 1
        i += 1
        
        child = self.read_node(node.children[i])
        if child.num_keys == 19:
            self._split_child(node, i, child)
            if key > node.keys[i]:
                i += 1
                child = self.read_node(node.children[i])
                
        return self._insert_non_full(child, key, value)

    def search(self, key):
        root_id, _ = self.read_header()
        if root_id == 0:
            return None
            
        current_node = self.read_node(root_id)
        
        while current_node:
            for i in range(current_node.num_keys):
                if key == current_node.keys[i]:
                    return current_node.values[i]
                if key < current_node.keys[i]:
                    current_node = self.read_node(current_node.children[i])
                    break
            else:
                current_node = self.read_node(current_node.children[current_node.num_keys])
                
        return None

    def print_tree(self):
        root_id, _ = self.read_header()
        if root_id == 0:
            print("Tree is empty")
            return
            
        def inorder(node_id):
            if node_id == 0:
                return
            node = self.read_node(node_id)
            i = 0
            while i < node.num_keys:
                inorder(node.children[i])
                print(f"Key: {node.keys[i]}, Value: {node.values[i]}")
                i += 1
            inorder(node.children[i])
            
        inorder(root_id)

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                success_count = 0
                error_count = 0
                for line in f:
                    try:
                        key, value = map(int, line.strip().split(','))
                        if key < 0 or value < 0:
                            error_count += 1
                            print(f"Skipping negative number in line: {line.strip()}")
                            continue
                        if self.insert(key, value):
                            success_count += 1
                        else:
                            error_count += 1
                            print(f"Skipping duplicate key: {key}")
                    except ValueError:
                        error_count += 1
                        print(f"Skipping invalid line: {line.strip()}")
                
                print(f"Load complete: {success_count} pairs inserted, {error_count} errors")
        except FileNotFoundError:
            print("Error: File not found")
        except Exception as e:
            print(f"Error loading file: {e}")

    def extract_to_file(self, filename):
        try:
            if os.path.exists(filename):
                response = input("File already exists. Overwrite? (y/n): ")
                if response.lower() != 'y':
                    print("Operation cancelled")
                    return

            root_id, _ = self.read_header()
            if root_id == 0:
                print("Tree is empty")
                return

            pairs = []
            def collect_pairs(node_id):
                if node_id == 0:
                    return
                node = self.read_node(node_id)
                i = 0
                while i < node.num_keys:
                    collect_pairs(node.children[i])
                    pairs.append((node.keys[i], node.values[i]))
                    i += 1
                collect_pairs(node.children[i])

            collect_pairs(root_id)

            with open(filename, 'w') as f:
                for key, value in pairs:
                    f.write(f"{key},{value}\n")
            
            print(f"Successfully exported {len(pairs)} pairs to {filename}")
        except Exception as e:
            print(f"Error extracting to file: {e}")

def display_menu():
    print("\nIndex File Management System")
    print("CREATE - Create a new index file")
    print("OPEN - Open an existing index file")
    print("INSERT - Insert a key/value pair")
    print("SEARCH - Search for a key")
    print("LOAD - Load pairs from file")
    print("PRINT - Print all key/value pairs")
    print("EXTRACT - Save pairs to file")
    print("QUIT - Exit program")

def main():
    manager = IndexFileManager()
    
    while True:
        display_menu()
        command = input("\nEnter command: ").upper().strip()
        
        if command == "QUIT":
            break
        elif command == "CREATE":
            filename = input("Enter filename: ")
            manager.create_file(filename)
        elif command == "OPEN":
            filename = input("Enter filename: ")
            manager.open_file(filename)
        elif command == "INSERT":
            if not manager.current_file:
                print("Error: No index file is currently open")
                continue
            try:
                key = int(input("Enter key: "))
                value = int(input("Enter value: "))
                if key < 0 or value < 0:
                    print("Error: Keys and values must be unsigned integers")
                    continue
                if manager.insert(key, value):
                    print("Insert successful")
                else:
                    print("Error: Key already exists")
            except ValueError:
                print("Error: Keys and values must be unsigned integers")
        elif command == "SEARCH":
            if not manager.current_file:
                print("Error: No index file is currently open")
                continue
            try:
                key = int(input("Enter key: "))
                if key < 0:
                    print("Error: Key must be an unsigned integer")
                    continue
                result = manager.search(key)
                if result is not None:
                    print(f"Key: {key}, Value: {result}")
                else:
                    print("Error: Key not found")
            except ValueError:
                print("Error: Key must be an unsigned integer")
        elif command == "LOAD":
            if not manager.current_file:
                print("Error: No index file is currently open")
                continue
            filename = input("Enter input filename: ")
            manager.load_from_file(filename)
        elif command == "PRINT":
            if not manager.current_file:
                print("Error: No index file is currently open")
                continue
            manager.print_tree()
            
        elif command == "EXTRACT":
            if not manager.current_file:
                print("Error: No index file is currently open")
                continue
            filename = input("Enter output filename: ")
            manager.extract_to_file(filename)
        else:
            print("Error: Invalid command")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")