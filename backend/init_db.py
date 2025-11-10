"""
Initialize Database with Sample Data
"""
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.vector_db import vector_db_service


def load_sample_data(file_path: str):
    """Load sample novels from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Initialize database with sample data"""
    print("=" * 60)
    print("웹소설 추천 시스템 - 데이터베이스 초기화")
    print("=" * 60)

    # Load sample data
    sample_data_path = Path(__file__).parent.parent / "data" / "sample_novels.json"

    if not sample_data_path.exists():
        print(f"❌ 샘플 데이터 파일을 찾을 수 없습니다: {sample_data_path}")
        return

    print(f"\n📂 샘플 데이터 로딩 중: {sample_data_path}")
    novels = load_sample_data(sample_data_path)
    print(f"✅ {len(novels)}개의 웹소설 데이터를 불러왔습니다.")

    # Initialize database
    print("\n🔧 ChromaDB 초기화 중...")
    print("⚠️  이 과정은 임베딩 모델을 다운로드하므로 시간이 걸릴 수 있습니다.")

    try:
        vector_db_service.add_novels(novels)
        print("\n✅ 데이터베이스 초기화 완료!")

        # Verify
        count = vector_db_service.count_novels()
        print(f"📊 총 {count}개의 소설이 데이터베이스에 저장되었습니다.")

        # Test search
        print("\n🔍 테스트 검색 실행 중...")
        test_query = "회귀해서 복수하는 판타지 소설"
        results = vector_db_service.search_novels(test_query, limit=3)

        print(f"\n검색어: '{test_query}'")
        print(f"검색 결과: {len(results)}개\n")

        for i, novel in enumerate(results[:3], 1):
            print(f"{i}. {novel['title']} (유사도: {novel['similarity_score']:.2%})")
            print(f"   작가: {novel['author']}")
            print(f"   키워드: {', '.join(novel['keywords'][:3])}")
            print()

        print("=" * 60)
        print("✨ 초기화가 성공적으로 완료되었습니다!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
