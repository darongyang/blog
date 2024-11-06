import subprocess
import time

while True:
    # Run the 'git push' command
    result = subprocess.run(['git', 'push'], capture_output=True, text=True)
    
    # Check if the result contains the word 'unable' (indicating failure)
    if "unable" in str(result.stderr):
        print(str(result.stderr))
        time.sleep(1)  # Wait 1 seconds before retrying
    else:
        print("Push succeeded!")
        break
