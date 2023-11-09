from rich.console import Console

console = Console()

def error(title,message,Environment_Information=None):
    """
    This function displays an error message in the console with a specific format.
    
    Parameters:
    - title (str): The main title for the error.
    - message (str): A detailed error message.
    - Environment_Information (str or dict, optional): Additional information about the environment 
      which could either be a string or a dictionary.
    """
    # Adjust the number of '-' characters based on the length of the title to maintain 
    # a consistent output width.
    if len(title) >= 57:
        line = '-' * 3
    else:
        line = '-' * (57 - len(title))
    
    # Print the title followed by the appropriate number of '-' characters.
    console.print(f"\n {title} {line}", style="yellow")
    
    # Print the detailed error message.
    console.print(f"\n  {message}")
    
    # If Environment_Information is provided, format and print it.
    if Environment_Information is not None:
        
        # If the environment information is a string:
        if isinstance(Environment_Information, str):
            # This line is redundant since it just converts a string to a string.
            # Environment_Information = str(Environment_Information)
            
            # Add indents to any new lines in the environment info for better formatting.
            Environment_Information = Environment_Information.replace('\n', '\n       ')
            
            # Print the formatted environment information.
            console.print('\n     Your Environment Information ---------------------------', style="yellow")
            console.print(f'       {Environment_Information}', style="yellow")
        
        # If the environment information is a dictionary:
        elif isinstance(Environment_Information, dict):
            console.print('\n     Your Environment Information ---------------------------', style="yellow")
            
            # Iterate through the dictionary and print each key-value pair.
            for key, value in Environment_Information.items():
                console.print(f'       {key}: {value}', style="yellow")

def warning_message(message):
    console.print(f"WARNING: {message}", style="bold yellow")

if __name__ == '__main__':
    message = """An error occurred: HelloLambdaFunction - Resource handler returned message: "Value nodejs12.xa at 'runtime' failed to satisfy constraint: Member must satisfy enum value set: [nodejs12.x, python3.6, provided, nodejs14.x, ruby2.7, java11, go1.x, provided.al2, java8, java8.al2, dotnetcore3.1, python3.7, python3.8] or be a valid ARN"""
    info = """Operating System: darwin
Node Version: 15.14.0
Framework Version: 2.52.1
Plugin Version: 5.4.3
SDK Version: 4.2.5
Components Version: 3.14.0"""
    error("Serverless Error",message,info)
    message = """An error occurred: HelloLambdaFunction - Resource handler returned message: "Value nodejs12.xa at 'runtime' failed to satisfy constraint: Member must satisfy enum value set: [nodejs12.x, python3.6, provided, nodejs14.x, ruby2.7, java11, go1.x, provided.al2, java8, java8.al2, dotnetcore3.1, python3.7, python3.8] or be a valid ARN"""
    info = {"Operating System": "darwin",
           "Node Version": "15.14.0",
           "Framework Version": "2.52.1",
           "Plugin Version": "5.4.3",
           "SDK Version": "4.2.5",
           "Components Version": "3.14.0"}
    error("Serverless Error",message,info)