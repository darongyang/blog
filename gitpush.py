import subprocess
import time

while True:
    # Run the 'git push' command
    result = subprocess.run(['git', 'push'], capture_output=True, text=True)
    
    # Print the result of the push
    print(result.stdout)
    
    # Check if the result contains the word 'unable' (indicating failure)
    if 'unable' in result.stdout:
        print("Push failed, retrying...")
        time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Push succeeded!")
        break
