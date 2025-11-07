"""
OpenSearch 검색 서비스
특허 및 논문 검색 기능
"""
from patents.opensearch_client import get_opensearch_client


class OpenSearchService:
    """OpenSearch 검색 서비스"""

    def __init__(self):
        self.client = get_opensearch_client()

    def search_patents(self, keyword, search_fields=None, filters=None, page=1, page_size=10, sort_by='relevance'):
        """
        특허 검색

        Args:
            keyword: 검색 키워드
            search_fields: 검색할 필드 리스트 (예: ['title', 'abstract', 'claims'])
            filters: 필터 조건 딕셔너리
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 결과 수
            sort_by: 정렬 방식 ('relevance'=관련도순, 'date_desc'=최신순, 'date_asc'=오래된순)

        Returns:
            dict: 검색 결과 및 메타데이터
        """
        # 기본 검색 필드
        if not search_fields:
            search_fields = ['title', 'abstract']

        # 검색 쿼리 구성
        must_queries = []

        # 키워드 검색 (정확한 매칭, 모든 단어 포함)
        if keyword:
            must_queries.append({
                'multi_match': {
                    'query': keyword,
                    'fields': search_fields,
                    'type': 'best_fields',
                    'operator': 'and'  # 모든 단어 포함 필요
                    # fuzziness 제거 - 정확한 매칭만
                }
            })

        # 필터 조건 추가
        filter_queries = []
        if filters:
            # IPC/CPC 코드 필터
            if filters.get('ipc_code'):
                filter_queries.append({
                    'wildcard': {
                        'ipc_code': f"*{filters['ipc_code']}*"
                    }
                })

            # 출원일 범위 필터
            if filters.get('application_start_date') or filters.get('application_end_date'):
                date_range = {}
                if filters.get('application_start_date'):
                    date_range['gte'] = filters['application_start_date']
                if filters.get('application_end_date'):
                    date_range['lte'] = filters['application_end_date']

                filter_queries.append({
                    'range': {
                        'application_date': date_range
                    }
                })

            # 등록일 범위 필터
            if filters.get('registration_start_date') or filters.get('registration_end_date'):
                date_range = {}
                if filters.get('registration_start_date'):
                    date_range['gte'] = filters['registration_start_date']
                if filters.get('registration_end_date'):
                    date_range['lte'] = filters['registration_end_date']

                filter_queries.append({
                    'range': {
                        'registration_date': date_range
                    }
                })

            # 법적상태 필터
            if filters.get('legal_status'):
                filter_queries.append({
                    'term': {
                        'legal_status': filters['legal_status']
                    }
                })

        # 최종 쿼리 구성
        if must_queries:
            query = {
                'bool': {
                    'must': must_queries,
                    'filter': filter_queries
                }
            }
        elif filter_queries:
            # 키워드 없이 필터만 있는 경우
            query = {
                'bool': {
                    'must': {'match_all': {}},
                    'filter': filter_queries
                }
            }
        else:
            # 키워드도 필터도 없는 경우
            query = {'match_all': {}}

        # 페이지네이션
        from_index = (page - 1) * page_size

        # 정렬 방식 설정
        if sort_by == 'relevance':
            # 관련도순 (키워드 검색에만 의미있음)
            sort_order = [
                {'_score': {'order': 'desc'}},
                {'application_date': {'order': 'desc', 'missing': '_last'}}  # 동점일 때 최신순
            ]
        elif sort_by == 'date_asc':
            # 오래된순
            sort_order = [
                {'application_date': {'order': 'asc', 'missing': '_last'}},
                {'_score': {'order': 'desc'}}  # 동점일 때 관련도순
            ]
        else:  # date_desc (기본값)
            # 최신순
            sort_order = [
                {'application_date': {'order': 'desc', 'missing': '_last'}},
                {'_score': {'order': 'desc'}}  # 동점일 때 관련도순
            ]

        # OpenSearch 검색 실행
        body = {
            'query': query,
            'from': from_index,
            'size': page_size,
            'sort': sort_order,
            'track_total_hits': True,  # 정확한 총 개수 추적
        }

        # 키워드 검색 시 최소 스코어 필터 적용 (관련 없는 결과 제외)
        if keyword:
            body['min_score'] = 1.0  # 최소 스코어 1.0 이상만 반환

        response = self.client.search(index='patents', body=body)

        # 결과 파싱
        hits = response['hits']
        total_count = hits['total']['value']
        total_pages = (total_count + page_size - 1) // page_size

        results = []
        for hit in hits['hits']:
            source = hit['_source']
            score = hit['_score']

            # 검색어가 있을 때 점수 로깅 (디버깅용)
            if keyword:
                print(f"[검색 점수] {score:.2f} - {source.get('title', '')[:50]}")

            result = {
                'id': hit['_id'],
                'title': source.get('title'),
                'title_en': source.get('title_en'),
                'application_number': source.get('application_number'),
                'application_date': source.get('application_date'),
                'applicant': source.get('applicant'),
                'registration_number': source.get('registration_number'),
                'registration_date': source.get('registration_date'),
                'ipc_code': source.get('ipc_code'),
                'cpc_code': source.get('cpc_code'),
                'abstract': source.get('abstract'),
                'claims': source.get('claims'),
                'legal_status': source.get('legal_status'),
                'score': score
            }
            results.append(result)

        return {
            'results': results,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'page_size': page_size
        }

    def search_papers(self, keyword, search_fields=None, filters=None, page=1, page_size=10, sort_by='relevance'):
        """
        논문 검색

        Args:
            keyword: 검색 키워드
            search_fields: 검색할 필드 리스트 (예: ['title_kr', 'abstract_kr'])
            filters: 필터 조건 딕셔너리
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 결과 수
            sort_by: 정렬 방식 ('relevance'=관련도순, 'date_desc'=최신순, 'date_asc'=오래된순)

        Returns:
            dict: 검색 결과 및 메타데이터
        """
        # 기본 검색 필드
        if not search_fields:
            search_fields = ['title_kr', 'abstract_kr']

        # 검색 쿼리 구성
        must_queries = []

        # 키워드 검색 (정확한 매칭, 모든 단어 포함)
        if keyword:
            must_queries.append({
                'multi_match': {
                    'query': keyword,
                    'fields': search_fields,
                    'type': 'best_fields',
                    'operator': 'and'  # 모든 단어 포함 필요
                    # fuzziness 제거 - 정확한 매칭만
                }
            })

        # 필터 조건 추가
        filter_queries = []
        if filters:
            # 발행일 범위 필터
            if filters.get('publication_start_date') or filters.get('publication_end_date'):
                date_range = {}
                if filters.get('publication_start_date'):
                    date_range['gte'] = filters['publication_start_date']
                if filters.get('publication_end_date'):
                    date_range['lte'] = filters['publication_end_date']

                filter_queries.append({
                    'range': {
                        'published_date': date_range
                    }
                })

        # 최종 쿼리 구성
        if must_queries:
            query = {
                'bool': {
                    'must': must_queries,
                    'filter': filter_queries
                }
            }
        elif filter_queries:
            # 키워드 없이 필터만 있는 경우
            query = {
                'bool': {
                    'must': {'match_all': {}},
                    'filter': filter_queries
                }
            }
        else:
            # 키워드도 필터도 없는 경우
            query = {'match_all': {}}

        # 페이지네이션
        from_index = (page - 1) * page_size

        # 정렬 순서 설정
        if sort_by == 'relevance':
            # 관련도순 (키워드 검색에만 의미있음)
            sort_order = [
                {'_score': {'order': 'desc'}},
                {'published_date': {'order': 'desc', 'missing': '_last'}},  # 동점일 때 최신순
                {'created_at': {'order': 'desc'}}
            ]
        elif sort_by == 'date_asc':
            # 오래된순
            sort_order = [
                {'published_date': {'order': 'asc', 'missing': '_last'}},
                {'created_at': {'order': 'asc'}},
                {'_score': {'order': 'desc'}}  # 동점일 때 관련도순
            ]
        else:  # date_desc (기본값)
            # 최신순
            sort_order = [
                {'published_date': {'order': 'desc', 'missing': '_last'}},
                {'created_at': {'order': 'desc'}},
                {'_score': {'order': 'desc'}}  # 동점일 때 관련도순
            ]

        # OpenSearch 검색 실행
        body = {
            'query': query,
            'from': from_index,
            'size': page_size,
            'sort': sort_order,
            'track_total_hits': True,  # 정확한 총 개수 추적
        }

        # 키워드 검색 시 최소 스코어 필터 적용 (관련 없는 결과 제외)
        if keyword:
            body['min_score'] = 1.0  # 최소 스코어 1.0 이상만 반환

        response = self.client.search(index='papers', body=body)

        # 결과 파싱
        hits = response['hits']
        total_count = hits['total']['value']
        total_pages = (total_count + page_size - 1) // page_size

        results = []
        for hit in hits['hits']:
            source = hit['_source']
            result = {
                'id': hit['_id'],
                'title_en': source.get('title_en'),
                'title_kr': source.get('title_kr'),
                'authors': source.get('authors'),
                'abstract_en': source.get('abstract_en'),
                'abstract_kr': source.get('abstract_kr'),
                'abstract_page_link': source.get('abstract_page_link'),
                'pdf_link': source.get('pdf_link'),
                'source_file': source.get('source_file'),
                'published_date': source.get('published_date'),
                'score': hit['_score']
            }
            results.append(result)

        return {
            'results': results,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'page_size': page_size
        }

    def get_patent_by_id(self, patent_id):
        """
        특허 ID로 상세 정보 조회
        """
        try:
            response = self.client.get(index='patents', id=patent_id)
            return response['_source']
        except Exception as e:
            print(f"특허 조회 오류 ({patent_id}): {e}")
            return None

    def get_paper_by_id(self, paper_id):
        """
        논문 ID로 상세 정보 조회
        """
        try:
            response = self.client.get(index='papers', id=paper_id)
            return response['_source']
        except Exception as e:
            print(f"논문 조회 오류 ({paper_id}): {e}")
            return None
