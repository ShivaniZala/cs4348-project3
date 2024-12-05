def display_menu():
    print("\nIndex File Management System")
    print("1. create - Create a new index file")
    print("2. open - Open an existing index file")
    print("3. quit - Exit program")

def main():
    while True:
        display_menu()
        command = input("\nEnter command: ").lower().strip()
        
        if command == "quit":
            break
        else:
            print("Command not implemented yet")

if __name__ == "__main__":
    main()