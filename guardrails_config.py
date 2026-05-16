import pexpect
import sys

token = open('.env').read().split('GUARDRAILS_API_KEY=')[1].strip()

child = pexpect.spawn('.venv/bin/guardrails configure')
child.logfile = sys.stdout.buffer

try:
    index = child.expect(['Enable anonymous metrics reporting\?', 'Do you wish to use remote inferencing\?', 'What is your token\?', pexpect.EOF, pexpect.TIMEOUT], timeout=3)
    if index == 0:
        child.sendline('n')
        index = child.expect(['Do you wish to use remote inferencing\?', 'What is your token\?', pexpect.EOF], timeout=3)
        if index == 0:
            child.sendline('n')
            index = child.expect(['What is your token\?', pexpect.EOF], timeout=3)
            if index == 0:
                child.sendline(token)
                child.expect(pexpect.EOF)
except Exception as e:
    print(f"Error: {e}")
