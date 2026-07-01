import tempfile
from pathlib import Path

import pytest

from bujji.tools.base import ToolRegistry
from bujji.tools.filesystem import FilesystemTool
from bujji.tools.python_exec import PythonExecTool
from bujji.tools.terminal import TerminalTool


@pytest.mark.asyncio
class TestToolRegistry:
    async def test_register_and_list(self):
        registry = ToolRegistry()
        tool = FilesystemTool()
        registry.register(tool)

        listed = registry.list_tools()
        assert len(listed) == 1
        assert listed[0].name == "filesystem"

        assert registry.get("filesystem") is tool
        assert registry.get("nonexistent") is None

    def test_get_schemas(self):
        registry = ToolRegistry()
        registry.register(FilesystemTool())
        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert "function" in schemas[0].get("type", schemas[0].get("function", {}))

    def test_unregister(self):
        registry = ToolRegistry()
        registry.register(FilesystemTool())
        assert len(registry) == 1
        registry.unregister("filesystem")
        assert len(registry) == 0


@pytest.mark.asyncio
class TestFilesystemTool:
    async def test_write_and_read(self):
        tool = FilesystemTool()
        with tempfile.TemporaryDirectory() as tmp:
            test_file = Path(tmp) / "test.txt"
            result = await tool.execute(
                operation="write", path=str(test_file), content="hello world"
            )
            assert result.success

            result = await tool.execute(operation="read", path=str(test_file))
            assert result.success
            assert "hello world" in result.output

    async def test_list_directory(self):
        tool = FilesystemTool()
        with tempfile.TemporaryDirectory() as tmp:
            result = await tool.execute(operation="list", path=tmp)
            assert result.success

    async def test_exists(self):
        tool = FilesystemTool()
        with tempfile.TemporaryDirectory() as tmp:
            result = await tool.execute(operation="exists", path=tmp)
            assert result.success
            assert result.output == "True"

    async def test_nonexistent_path(self):
        tool = FilesystemTool()
        result = await tool.execute(
            operation="read", path="/nonexistent/bujji_test_file_xyz"
        )
        assert not result.success


@pytest.mark.asyncio
class TestPythonExecTool:
    async def test_simple_execution(self):
        tool = PythonExecTool()
        result = await tool.execute(code="print('hello from bujji')")
        assert result.success
        assert "hello from bujji" in result.output

    async def test_execution_with_error(self):
        tool = PythonExecTool()
        result = await tool.execute(code="raise ValueError('test error')")
        assert not result.success

    async def test_math_execution(self):
        tool = PythonExecTool()
        result = await tool.execute(code="print(2 + 2)")
        assert result.success
        assert "4" in result.output


@pytest.mark.asyncio
class TestTerminalTool:
    async def test_echo(self):
        tool = TerminalTool()
        result = await tool.execute(
            command="echo hello from bujji", timeout=10
        )
        assert result.success
        assert "hello from bujji" in result.output

    async def test_failing_command(self):
        tool = TerminalTool()
        result = await tool.execute(
            command="exit 1", timeout=10
        )
        assert not result.success
