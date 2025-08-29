# IntelliJ IDEA Setup Instructions

## Configuring Python SDK for the Virtual Environment

Since IntelliJ IDEA needs to be configured interactively, follow these steps:

### 1. Open the Module in IntelliJ IDEA

1. Open IntelliJ IDEA
2. Go to **File** → **Open** and select the `event-bridge-stepfunction-lambda` folder
3. Or if already in the parent project, the module should appear in the project tree

### 2. Configure Python SDK

1. Go to **File** → **Project Structure** (Ctrl/Cmd + Alt + Shift + S)
2. In the left panel, click **Modules**
3. Select the `event-bridge-stepfunction-lambda` module
4. In the **Dependencies** tab, click the **Module SDK** dropdown
5. Select **Add SDK** → **Python SDK**
6. Choose **Virtualenv Environment** → **Existing environment**
7. Set the interpreter path to:
   ```
   /Users/kourla/IdeaProjects/aws-learning-examples/event-bridge-stepfunction-lambda/venv/bin/python
   ```
8. Click **OK**

### 3. Alternative Method - Through Settings

1. Go to **File** → **Settings** (or **IntelliJ IDEA** → **Preferences** on macOS)
2. Navigate to **Project: aws-learning-examples** → **Python Interpreter**
3. Click the gear icon → **Add...**
4. Select **Virtualenv Environment** → **Existing environment**
5. Browse to: `/Users/kourla/IdeaProjects/aws-learning-examples/event-bridge-stepfunction-lambda/venv/bin/python`
6. Name it: `Python 3.9 (event-bridge-stepfunction-lambda)`
7. Click **OK**

### 4. Verify Setup

After configuration, verify that:
- The Python interpreter shows as `Python 3.9 (event-bridge-stepfunction-lambda)`
- You can see installed packages like `aws-cdk-lib`, `boto3`, etc.
- Code completion works for imports like `import boto3`

### 5. Mark Directories

Ensure these directories are marked correctly:
- `lambda_functions/` - **Sources Root**
- `cdk_stack/` - **Sources Root** 
- `venv/` - **Excluded**
- `cdk.out/` - **Excluded**

### 6. Run Configuration

To create run configurations:
1. Right-click on `app.py` → **Create 'app'**
2. Or go to **Run** → **Edit Configurations**
3. Add new **Python** configuration
4. Set **Script path** to: `app.py`
5. Set **Working directory** to: `/Users/kourla/IdeaProjects/aws-learning-examples/event-bridge-stepfunction-lambda`
6. Ensure **Python interpreter** is set to the virtual environment

## Testing the Setup

1. Try importing boto3 in a Python file - should have code completion
2. Open `lambda_functions/event_generator/lambda_function.py` - should have proper syntax highlighting
3. Run `app.py` to synthesize the CDK app (won't deploy without AWS credentials)

## AWS Credentials Configuration

For IntelliJ to recognize AWS credentials:
1. Go to **File** → **Settings** → **Tools** → **AWS Connection Settings**
2. Choose your credential provider (Profile, Environment Variables, etc.)
3. Or set environment variables in run configurations:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION`