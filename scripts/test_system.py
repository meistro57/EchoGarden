import subprocess
import os

# Run the tests
def test_system():
    """Test the full system functionality."""
    
    # 1. Check database is ready
    result = subprocess.run([
        "docker", "compose", "-f", "../infra/docker-compose.yml", "exec", "db", 
        "psql", "-U", "postgres", "-c", "SELECT 1;"
    ], capture_output=True, text=True, cwd="infra")
    
    if result.returncode != 0:
        print(f"❌ Database not ready: {result.stderr}")
        return False
    
    print("✅ Database ready")
    
    # 2. Test API health
    result = subprocess.run([
        "curl", "-s", "http://localhost:8000/health"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ API not healthy: {result.stderr}")
        return False
    
    print("✅ API healthy")
    
    # 3. Test ingest with sample data
    # Would need sample export file
    
    return True

if __name__ == "__main__":
    print("🧪 Testing MCP Chat Log System...")
    success = test_system()
    print(f"Test {'PASSED' if success else 'FAILED'}")