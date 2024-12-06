# cs4348-project3
# CS4348 Project 3: B-Tree Index File Management System

## Files
- `btree.py` - Main program file containing the B-tree implementation

## How to Run
1. Ensure Python is installed on your system
2. Open command prompt/terminal
3. Navigate to the project directory 
4. Type: python btree.py

## Available Commands
All commands are case-insensitive:
- CREATE - Create a new index file
- OPEN - Open an existing index file
- INSERT - Insert a key/value pair
- SEARCH - Search for a key
- LOAD - Load pairs from file
- PRINT - Print all key/value pairs
- EXTRACT - Save pairs to file
- QUIT - Exit program

## Testing
To test the program:
1. Create a test.csv file with pairs of numbers separated by commas
2. Run the program
3. Create or open an index file
4. Try each command to verify functionality
5. Check results with PRINT command

## Implementation Details
- Uses B-tree with minimum degree 10
- Files divided into 512-byte blocks
- Maximum of 3 nodes in memory
- Big-endian byte order for integers
- Header contains magic number, root ID, and next block ID

## Important Notes
- Only unsigned integers are accepted for keys and values
- Files must be opened before using commands (except CREATE, OPEN, QUIT)
- CSV files must have one key-value pair per line, separated by a comma
- Program validates all inputs and handles errors appropriately
- Maintains three-node memory limit