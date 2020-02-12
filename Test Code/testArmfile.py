def listener(): 
    command = ""
    
    while(command == ""):
        command = input("Please enter a command: ")

    print(command)

    if (command != "exit"):
        listener()


# Main
listener()

