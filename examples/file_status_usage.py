"""
示例：如何使用 File 模型和 FileStatus 枚举
"""

from infrastructure.database.models.file import File, FileStatus
from infrastructure.database.repositories.file import FileRepository
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import asyncio


async def demonstrate_file_status_usage():
    """演示 File 状态的使用方法"""
    
    # 1. 创建文件实例
    print("=== 创建文件实例 ===")
    file = File(
        original_name="document.pdf",
        file_size=1024 * 1024,  # 1MB
        content_type="application/pdf",
        storage_bucket="my-bucket",
        storage_key="uploads/document.pdf",
        topic_id=1
    )
    
    print(f"文件初始状态: {file.status}")
    print(f"是否可用: {file.is_available}")
    print(f"是否处理中: {file.is_processing}")
    
    # 2. 状态转换
    print("\n=== 状态转换 ===")
    
    # 标记为处理中
    file.mark_as_processing()
    print(f"标记为处理中后: {file.status}")
    print(f"是否处理中: {file.is_processing}")
    
    # 标记为可用
    file.mark_as_available()
    print(f"标记为可用后: {file.status}")
    print(f"是否可用: {file.is_available}")
    
    # 标记为失败
    file.mark_as_failed()
    print(f"标记为失败后: {file.status}")
    print(f"是否失败: {file.is_failed}")
    
    # 3. 使用 Repository 方法
    print("\n=== Repository 方法使用 ===")
    
    # 模拟数据库会话（实际使用时需要真实的数据库连接）
    # engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
    # async_session = sessionmaker(engine, class_=AsyncSession)
    
    # 创建 mock repository 来演示
    class MockFileRepository(FileRepository):
        def __init__(self):
            self.files = {}
        
        async def get(self, file_id: str):
            return self.files.get(file_id)
        
        async def session(self):
            return None
        
        async def commit(self):
            pass
        
        async def refresh(self, entity):
            pass
    
    repo = MockFileRepository()
    
    # 4. 状态查询示例
    print("\n=== 状态查询示例 ===")
    
    # 创建多个不同状态的文件
    files_data = [
        {"id": "1", "status": FileStatus.UPLOADING, "name": "file1.pdf"},
        {"id": "2", "status": FileStatus.AVAILABLE, "name": "file2.pdf"},
        {"id": "3", "status": FileStatus.PROCESSING, "name": "file3.pdf"},
        {"id": "4", "status": FileStatus.FAILED, "name": "file4.pdf"},
        {"id": "5", "status": FileStatus.AVAILABLE, "name": "file5.pdf"},
    ]
    
    for data in files_data:
        file_obj = File(
            id=data["id"],
            original_name=data["name"],
            file_size=1024,
            content_type="application/pdf",
            storage_bucket="bucket",
            storage_key=f"uploads/{data['name']}",
            status=data["status"]
        )
        repo.files[data["id"]] = file_obj
    
    # 5. 状态统计
    print("\n=== 状态统计 ===")
    status_counts = {}
    for status in FileStatus:
        count = sum(1 for f in repo.files.values() if f.status == status)
        status_counts[status.value] = count
    
    for status, count in status_counts.items():
        print(f"{status}: {count} 个文件")
    
    # 6. 状态过滤示例
    print("\n=== 状态过滤示例 ===")
    
    # 获取所有可用的文件
    available_files = [f for f in repo.files.values() if f.status == FileStatus.AVAILABLE]
    print(f"可用文件数量: {len(available_files)}")
    
    # 获取所有处理中的文件
    processing_files = [f for f in repo.files.values() if f.status == FileStatus.PROCESSING]
    print(f"处理中文件数量: {len(processing_files)}")
    
    # 获取所有失败的文件
    failed_files = [f for f in repo.files.values() if f.status == FileStatus.FAILED]
    print(f"失败文件数量: {len(failed_files)}")


def demonstrate_enum_features():
    """演示 FileStatus 枚举的特性"""
    print("\n=== FileStatus 枚举特性 ===")
    
    # 1. 枚举值
    print(f"所有状态值: {[status.value for status in FileStatus]}")
    
    # 2. 枚举成员
    print(f"所有状态成员: {[status.name for status in FileStatus]}")
    
    # 3. 状态比较
    status1 = FileStatus.UPLOADING
    status2 = FileStatus.AVAILABLE
    
    print(f"\n状态比较:")
    print(f"{status1.value} == 'uploading': {status1.value == 'uploading'}")
    print(f"{status2.value} == 'available': {status2.value == 'available'}")
    
    # 4. 状态转换
    print(f"\n状态转换:")
    for status in FileStatus:
        print(f"{status.name} -> {status.value}")


if __name__ == "__main__":
    print("File 状态使用示例")
    print("=" * 50)
    
    # 演示枚举特性
    demonstrate_enum_features()
    
    # 演示文件状态使用
    asyncio.run(demonstrate_file_status_usage())
    
    print("\n" + "=" * 50)
    print("示例完成！")
