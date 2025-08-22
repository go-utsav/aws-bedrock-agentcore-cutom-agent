1. to create a project we have used UV librabry.

Create your agent project
Setting up your project
Create and navigate to your project directory:


mkdir my-custom-agent && cd my-custom-agent
Initialize the project with Python 3.11:


uv init --python 3.11
Add the required dependencies (uv automatically creates a .venv):


uv add fastapi 'uvicorn[standard]' pydantic httpx strands-agents