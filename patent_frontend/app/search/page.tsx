"use client"
import { API_BASE_URL } from "@/lib/config"

import { MainLayout } from "@/components/main-layout"
import { Search, ChevronDown, ChevronUp, Send, FileText, Upload, Download, Clock, X, Loader2, Paperclip } from "lucide-react"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"

interface Patent {
  id: number
  title: string
  applicationNumber: string
  applicationDate: string
  summary: string
  applicant?: string
  registrationNumber?: string
  registrationDate?: string
  ipcCode?: string
  cpcCode?: string
  claims?: string
  pdfLink?: string  // 논문 PDF 링크
  legalStatus?: string  // 법적상태
  highlight?: boolean
}

interface Paper {
  id: number
  title_kr: string
  title_en?: string
  authors: string
  abstract_kr: string
  abstract_en?: string
  abstract_page_link?: string
  pdf_link?: string
}

interface RejectReason {
  id: number
  doc_id: string
  send_number: string
  send_date: string
  applicant: string
  agent: string
  application_number: string
  invention_name: string
  examination_office: string
  examiner: string
  processed_text: string
}

interface OpinionDocument {
  id: number
  application_number: string
  full_text: string
  created_at: string
}

const SAMPLE_PATENTS: Patent[] = [
  {
    id: 1,
    title: "인공지능 기반 이미지 인식 방법 및 시스템",
    applicationNumber: "10-2024-0001234",
    applicationDate: "2024-01-15",
    summary:
      "본 발명은 인공지능 딥러닝 알고리즘을 활용하여 이미지를 자동으로 분석하고 객체를 인식하는 방법에 관한 것이다.",
  },
  {
    id: 2,
    title: "딥러닝을 활용한 자연어 처리 장치",
    applicationNumber: "10-2024-0002345",
    applicationDate: "2024-02-20",
    summary: "인공지능 기술을 이용한 자연어 처리 시스템으로, 사용자의 질의를 이해하고 적절한 응답을 생성한다.",
  },
  {
    id: 3,
    title: "인공지능 기반 의료 진단 보조 시스템",
    applicationNumber: "10-2024-0003456",
    applicationDate: "2024-03-10",
    summary: "의료 영상 데이터를 인공지능으로 분석하여 질병을 조기에 발견하고 진단을 보조하는 시스템이다.",
  },
  {
    id: 4,
    title: "머신러닝 기반 예측 모델 생성 방법",
    applicationNumber: "10-2024-0004567",
    applicationDate: "2024-04-05",
    summary:
      "인공지능 머신러닝 알고리즘을 사용하여 대량의 데이터로부터 패턴을 학습하고 미래를 예측하는 모델을 생성한다.",
  },
  {
    id: 5,
    title: "인공지능 챗봇 시스템 및 그 운영 방법",
    applicationNumber: "10-2024-0005678",
    applicationDate: "2024-05-12",
    summary: "사용자와 자연스러운 대화가 가능한 인공지능 기반 챗봇 시스템으로, 다양한 질문에 실시간으로 응답한다.",
  },
]

interface Message {
  id: number
  type: "user" | "ai" | "system"
  content: string
  file?: {
    name: string
    size: number
    type: string
  }
  metadata?: any
}

const INITIAL_MESSAGES: Message[] = [
  {
    id: 1,
    type: "ai",
    content: "안녕하세요! 특허 분석 AI 챗봇입니다. 특허 검색, 문서 분석, 질문 응답 등 다양한 도움을 드릴 수 있습니다. 무엇을 도와드릴까요?",
  },
]

// highlightText 함수 제거됨 - 검색어 하이라이트 기능 비활성화

export default function SearchPage() {
  const [searchType, setSearchType] = useState<"patent" | "paper">("patent")
  const [searchQuery, setSearchQuery] = useState("")
  const [searchInTitle, setSearchInTitle] = useState(true)
  const [searchInSummary, setSearchInSummary] = useState(false)
  const [searchInClaims, setSearchInClaims] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [ipcCode, setIpcCode] = useState("")
  const [applicationStartDate, setApplicationStartDate] = useState("")
  const [applicationEndDate, setApplicationEndDate] = useState("")
  const [publicationStartDate, setPublicationStartDate] = useState("")
  const [publicationEndDate, setPublicationEndDate] = useState("")
  const [legalStatusFilter, setLegalStatusFilter] = useState("")
  const [sortBy, setSortBy] = useState("date_desc")
  const [currentPage, setCurrentPage] = useState(1)
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES)
  const [inputMessage, setInputMessage] = useState("")
  const [searchResults, setSearchResults] = useState<Patent[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [isSearching, setIsSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [isUserSearched, setIsUserSearched] = useState(false)  // 사용자가 검색 버튼을 눌렀는지 여부
  const [isTyping, setIsTyping] = useState(false)
  const [activeTab, setActiveTab] = useState<"search" | "chat">("search")
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedPatentId, setSelectedPatentId] = useState<number | null>(null)
  const [patentDetails, setPatentDetails] = useState<Patent | null>(null)
  const [isLoadingDetails, setIsLoadingDetails] = useState(false)
  const [selectedPaperId, setSelectedPaperId] = useState<number | null>(null)
  const [paperDetails, setPaperDetails] = useState<Paper | null>(null)
  const [isPaperModalOpen, setIsPaperModalOpen] = useState(false)
  const [isLoadingPaperDetails, setIsLoadingPaperDetails] = useState(false)
  const [rejectReasons, setRejectReasons] = useState<RejectReason[]>([])
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false)
  const [isLoadingRejectReasons, setIsLoadingRejectReasons] = useState(false)
  const [rejectDocumentTab, setRejectDocumentTab] = useState<"specification" | "opinion">("specification")
  const [opinionDocuments, setOpinionDocuments] = useState<OpinionDocument[]>([])
  const [isLoadingOpinionDocuments, setIsLoadingOpinionDocuments] = useState(false)
  const [hasRejectData, setHasRejectData] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 채팅 자동 스크롤
  useEffect(() => {
    // 챗봇 탭이 활성화된 경우에만 스크롤
    if (activeTab === 'chat' && messagesContainerRef.current) {
      const scrollToBottom = () => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
        }
      }

      // 즉시 스크롤
      scrollToBottom()

      // DOM 업데이트 후 다시 스크롤 (이미지나 동적 콘텐츠 대비)
      setTimeout(scrollToBottom, 50)
      setTimeout(scrollToBottom, 200)
    }
  }, [messages.length, activeTab, isTyping])

  // 페이지 로드 시 스크롤을 맨 아래로
  useEffect(() => {
    if (messages.length > 0 && messagesContainerRef.current) {
      setTimeout(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
        }
      }, 300)
    }
  }, [])

  // 페이지 로드 시: URL 파라미터 확인 또는 localStorage에서 복원
  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search)
    const conversationIdParam = searchParams.get('conversation_id')
    const tabParam = searchParams.get('tab')

    if (conversationIdParam && tabParam === 'chat') {
      // URL에서 conversation_id가 있으면 서버에서 불러오기
      loadConversation(conversationIdParam)
      setActiveTab('chat')
    } else {
      // 없으면 localStorage에서 복원
      loadFromLocalStorage()
    }
  }, [])

  // 메시지나 conversationId가 변경될 때마다 localStorage에 저장
  useEffect(() => {
    saveToLocalStorage()
  }, [messages, conversationId])

  const saveToLocalStorage = () => {
    try {
      localStorage.setItem('chatbot_messages', JSON.stringify(messages))
      if (conversationId) {
        localStorage.setItem('chatbot_conversation_id', conversationId)
      }
    } catch (error) {
      console.error('localStorage 저장 실패:', error)
    }
  }

  const loadFromLocalStorage = () => {
    try {
      const savedMessages = localStorage.getItem('chatbot_messages')
      const savedConversationId = localStorage.getItem('chatbot_conversation_id')

      if (savedMessages) {
        const parsed = JSON.parse(savedMessages)
        // 초기 메시지가 아닌 경우에만 복원
        if (parsed.length > 1) {
          setMessages(parsed)
        }
      }

      if (savedConversationId) {
        setConversationId(savedConversationId)
      }
    } catch (error) {
      console.error('localStorage 로드 실패:', error)
    }
  }

  const startNewChat = () => {
    // 새 채팅 시작
    setMessages(INITIAL_MESSAGES)
    setConversationId(null)
    setInputMessage('')
    setUploadedFile(null)

    // localStorage 초기화
    localStorage.removeItem('chatbot_messages')
    localStorage.removeItem('chatbot_conversation_id')

    // URL 파라미터 제거
    window.history.pushState({}, '', '/search')
  }

  const loadConversation = async (convId: string) => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    if (!token) {
      alert("로그인이 필요합니다.")
      window.location.href = "/login"
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/chatbot/conversations/${convId}/`, {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) {
        throw new Error("대화를 불러오는데 실패했습니다.")
      }

      const data = await response.json()

      // 기존 메시지들을 변환하여 로드
      const loadedMessages: Message[] = data.messages.map((msg: any, index: number) => ({
        id: index + 1,
        type: msg.type as "user" | "ai" | "system",
        content: msg.content,
        file: msg.file_name ? {
          name: msg.file_name,
          size: 0,
          type: ""
        } : undefined
      }))

      setMessages(loadedMessages)
      setConversationId(convId)
    } catch (error) {
      console.error("대화 불러오기 오류:", error)
      alert("대화를 불러오는데 실패했습니다.")
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadedFile(file)
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && !uploadedFile) return

    const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    if (!token) {
      alert("로그인이 필요합니다.")
      window.location.href = "/login"
      return
    }

    const newUserMessage: Message = {
      id: Date.now(),
      type: "user",
      content: inputMessage || "파일을 업로드했습니다.",
      file: uploadedFile ? {
        name: uploadedFile.name,
        size: uploadedFile.size,
        type: uploadedFile.type,
      } : undefined,
    }

    setMessages([...messages, newUserMessage])
    const currentMessage = inputMessage
    const currentFile = uploadedFile
    setInputMessage("")
    setUploadedFile(null)

    // 메시지 추가 후 스크롤
    setTimeout(() => {
      if (messagesContainerRef.current) {
        messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
      }
    }, 100)

    // Show typing indicator
    setIsTyping(true)

    try {
      // 파일 내용 읽기 (텍스트 파일인 경우)
      let fileContent: string | null = null
      if (currentFile) {
        const fileText = await currentFile.text()
        fileContent = fileText
      }

      // API 호출
      const response = await fetch(`${API_BASE_URL}/api/chatbot/send/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: currentMessage || "파일을 업로드했습니다.",
          conversation_id: conversationId,
          file_content: fileContent,
          file_name: currentFile?.name,
        }),
      })

      if (!response.ok) {
        throw new Error("챗봇 응답을 받지 못했습니다.")
      }

      const data = await response.json()

      // 대화 ID 저장 (처음 대화인 경우)
      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id)
      }

      setIsTyping(false)

      // AI 응답 메시지 추가
      const aiResponse: Message = {
        id: Date.now() + 1,
        type: "ai",
        content: data.ai_message.content,
      }
      setMessages(prev => [...prev, aiResponse])

      // AI 응답 후 스크롤
      setTimeout(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
        }
      }, 100)

    } catch (error) {
      console.error("챗봇 오류:", error)
      setIsTyping(false)

      // 오류 메시지 표시
      const errorResponse: Message = {
        id: Date.now() + 1,
        type: "ai",
        content: "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
      }
      setMessages(prev => [...prev, errorResponse])

      // 오류 메시지 후 스크롤
      setTimeout(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
        }
      }, 100)
    }
  }

  const handleSendToChat = (patent: Patent) => {
    const systemMessage: Message = {
      id: Date.now(),
      type: "system",
      content: `특허 ${patent.applicationNumber} 정보 전송됨\n제목: ${patent.title}\n출원일: ${patent.applicationDate}`,
    }
    setMessages([...messages, systemMessage])
    setActiveTab("chat")
  }

  const handleAddToSearch = (patent: any) => {
    const newPatent: Patent = {
      id: Date.now(),
      title: patent.title,
      applicationNumber: patent.applicationNumber,
      applicationDate: patent.applicationDate,
      summary: patent.summary,
      highlight: true,
    }

    setSearchResults([newPatent, ...searchResults])
    setActiveTab("search")

    // Remove highlight after 2 seconds
    setTimeout(() => {
      setSearchResults((prev) => prev.map((p) => (p.id === newPatent.id ? { ...p, highlight: false } : p)))
    }, 2000)
  }

  // 전체 특허 목록 또는 검색 결과 가져오기
  const fetchPatents = async (keyword: string = '', page: number = 1, customSortBy?: string) => {
    setIsSearching(true)

    const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    try {
      let response;
      const endpoint = searchType === "paper" ? "/api/papers" : "/api/patents"

      // 검색 API를 사용할 조건: 키워드가 있거나 필터가 있을 때
      const hasSearchParams = keyword.trim() ||
        (searchType === "patent" && (ipcCode || applicationStartDate || applicationEndDate ||
         publicationStartDate || publicationEndDate || legalStatusFilter))

      if (hasSearchParams) {
        // 키워드 검색 또는 필터 검색
        let searchFields = []

        if (searchType === "paper") {
          // 논문 검색 필드
          if (searchInTitle) searchFields.push('title_kr')
          if (searchInSummary) searchFields.push('abstract_kr')
        } else {
          // 특허 검색 필드
          if (searchInTitle) searchFields.push('title')
          if (searchInSummary) searchFields.push('abstract')
          if (searchInClaims) searchFields.push('claims')
        }

        const requestBody: any = {
          keyword: keyword,
          search_fields: searchFields.length > 0 ? searchFields : (searchType === "paper" ? ['title_kr', 'abstract_kr'] : ['title', 'abstract']),
          page: page,
          page_size: 10
        }

        // 정렬 방식 추가 (특허 및 논문 공통)
        const sortByValue = customSortBy !== undefined ? customSortBy : sortBy
        if (sortByValue) requestBody.sort_by = sortByValue

        // 고급 필터
        if (searchType === "patent") {
          // 특허 전용 필터
          if (ipcCode) requestBody.ipc_code = ipcCode
          if (applicationStartDate) requestBody.application_start_date = applicationStartDate
          if (applicationEndDate) requestBody.application_end_date = applicationEndDate
          if (publicationStartDate) requestBody.registration_start_date = publicationStartDate
          if (publicationEndDate) requestBody.registration_end_date = publicationEndDate
          if (legalStatusFilter) requestBody.legal_status = legalStatusFilter
        } else {
          // 논문 전용 필터 (발행일 범위)
          if (applicationStartDate) requestBody.publication_start_date = applicationStartDate
          if (applicationEndDate) requestBody.publication_end_date = applicationEndDate
        }

        response = await fetch(`${API_BASE_URL}${endpoint}/search/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
          },
          body: JSON.stringify(requestBody)
        })
      } else {
        // 전체 목록 조회
        response = await fetch(`${API_BASE_URL}${endpoint}/?page=${page}&page_size=10`, {
          headers: {
            ...(token && { 'Authorization': `Bearer ${token}` })
          }
        })
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('API 에러:', response.status, errorData)
        throw new Error(`데이터 조회 실패 (${response.status})`)
      }

      const data = await response.json()
      console.log('API 응답 데이터:', data)

      // 백엔드 응답을 프론트엔드 형식으로 변환
      let patents: Patent[]
      let total: number
      let pages: number

      if (searchType === "paper") {
        // 논문 데이터 변환
        if (keyword.trim()) {
          patents = data.results.map((item: any) => ({
            id: item.id,
            title: item.title_kr,
            applicationNumber: item.authors || '',  // 저자를 applicationNumber에 표시
            applicationDate: item.published_date || '',  // 발행일
            summary: item.abstract_kr || '',
            pdfLink: item.pdf_link || ''  // PDF 링크 추가
          }))
          total = data.total_count || 0
          pages = data.total_pages || 0
        } else {
          patents = data.results.map((item: any) => ({
            id: item.id,
            title: item.title_kr,
            applicationNumber: item.authors || '',
            applicationDate: item.published_date || '',  // 발행일
            summary: item.abstract_kr || '',
            pdfLink: item.pdf_link || ''
          }))
          total = data.count || 0
          pages = Math.ceil(total / 10)
        }
      } else {
        // 특허 데이터 변환
        if (hasSearchParams) {
          // 검색 API 응답 (키워드 검색 또는 필터 사용 시)
          patents = data.results.map((item: any) => ({
            id: item.id,
            title: item.title,
            applicationNumber: item.application_number,
            applicationDate: item.application_date || '',
            summary: item.abstract || '',
            legalStatus: item.legal_status || ''
          }))
          total = data.total_count || 0
          pages = data.total_pages || 0
        } else {
          // 목록 API 응답 (커스텀 페이지네이션)
          patents = data.results.map((item: any) => ({
            id: item.id,
            title: item.title,
            applicationNumber: item.application_number,
            applicationDate: item.application_date || '',
            summary: item.abstract || '',
            legalStatus: item.legal_status || ''
          }))
          total = data.count || 0
          pages = data.total_pages || Math.ceil(total / 10)
        }
      }

      setSearchResults(patents)
      setTotalCount(total)
      setTotalPages(pages)
      setIsSearching(false)
      setHasSearched(true)
    } catch (error) {
      console.error('데이터 조회 오류:', error)
      setIsSearching(false)
      setHasSearched(true)
      setSearchResults([])
      setTotalCount(0)
      setTotalPages(0)
    }
  }

  // 법적상태 배지 렌더링
  const getLegalStatusBadge = (status?: string) => {
    if (!status) return null

    const statusConfig: Record<string, { color: string; bgColor: string; label: string }> = {
      '등록': { color: 'text-green-700', bgColor: 'bg-green-100', label: '등록' },
      '공개': { color: 'text-blue-700', bgColor: 'bg-blue-100', label: '공개' },
      '거절': { color: 'text-red-700', bgColor: 'bg-red-100', label: '거절' },
      '취하': { color: 'text-gray-700', bgColor: 'bg-gray-100', label: '취하' },
      '포기': { color: 'text-gray-700', bgColor: 'bg-gray-100', label: '포기' },
    }

    // "소멸" 포함 상태 처리
    if (status.includes('소멸')) {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-700">
          소멸
        </span>
      )
    }

    const config = statusConfig[status] || { color: 'text-gray-700', bgColor: 'bg-gray-100', label: status }

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.bgColor} ${config.color}`}>
        {config.label}
      </span>
    )
  }

  const handleSearch = () => {
    setCurrentPage(1)
    setIsUserSearched(true)  // 사용자가 검색 버튼을 눌렀음을 표시
    fetchPatents(searchQuery, 1)
  }

  const handlePageChange = (page: number) => {
    // 유효한 페이지 범위 확인
    if (page < 1 || (totalPages > 0 && page > totalPages)) {
      return
    }
    setCurrentPage(page)
    fetchPatents(searchQuery, page)
  }

  // 초기 로드 시 및 searchType 변경 시 데이터 가져오기
  useEffect(() => {
    setCurrentPage(1)
    setIsUserSearched(false)  // 검색 타입 변경 시 검색 카운트 숨김
    if (hasSearched && searchQuery) {
      // 검색어가 있으면 검색 실행
      fetchPatents(searchQuery, 1)
    } else {
      // 검색어가 없으면 전체 목록 조회
      fetchPatents('', 1)
    }
  }, [searchType])

  // 특허 상세 정보 가져오기
  const fetchPatentDetails = async (patentId: number) => {
    setIsLoadingDetails(true)
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    try {
      const response = await fetch(`${API_BASE_URL}/api/patents/${patentId}/`, {
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      })

      if (!response.ok) {
        throw new Error('특허 상세 정보 조회 실패')
      }

      const data = await response.json()

      const patentDetail: Patent = {
        id: data.id,
        title: data.title,
        applicationNumber: data.application_number,
        applicationDate: data.application_date || '',
        summary: data.abstract || '',
        applicant: data.applicant || '',
        registrationNumber: data.registration_number || '',
        registrationDate: data.registration_date || '',
        ipcCode: data.ipc_code || '',
        cpcCode: data.cpc_code || '',
        claims: data.claims || '',
        legalStatus: data.legal_status || ''
      }

      setPatentDetails(patentDetail)
      setIsLoadingDetails(false)
      return patentDetail
    } catch (error) {
      console.error('특허 상세 정보 조회 오류:', error)
      setIsLoadingDetails(false)
      alert('특허 상세 정보를 불러오는데 실패했습니다.')
      return null
    }
  }

  // 상세보기 버튼 클릭
  const handleViewDetails = async (patentId: number) => {
    setSelectedPatentId(patentId)
    setIsModalOpen(true)
    const details = await fetchPatentDetails(patentId)

    // 거절 데이터 존재 여부 미리 확인
    if (details?.applicationNumber) {
      checkRejectDataExists(details.applicationNumber)
    }
  }

  // 거절 데이터 존재 여부만 확인 (모달 열지 않음)
  const checkRejectDataExists = async (applicationNumber: string) => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    try {
      const response = await fetch(`${API_BASE_URL}/api/patents/reject-reasons/${applicationNumber}/`, {
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      })

      if (response.ok) {
        const data = await response.json()
        setHasRejectData(data.has_reject_reasons || false)
      } else {
        setHasRejectData(false)
      }
    } catch (error) {
      setHasRejectData(false)
    }
  }

  // 모달 닫기
  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedPatentId(null)
    setPatentDetails(null)
  }

  // 논문 상세 정보 가져오기
  const fetchPaperDetails = async (paperId: number) => {
    setIsLoadingPaperDetails(true)
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    try {
      const response = await fetch(`${API_BASE_URL}/api/papers/${paperId}/`, {
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      })

      if (!response.ok) {
        throw new Error('논문 상세 정보 조회 실패')
      }

      const data = await response.json()
      setPaperDetails(data)
      setIsLoadingPaperDetails(false)
    } catch (error) {
      console.error('논문 상세 정보 조회 오류:', error)
      setIsLoadingPaperDetails(false)
      alert('논문 상세 정보를 불러오는데 실패했습니다.')
    }
  }

  // 논문 상세보기 버튼 클릭
  const handleViewPaperDetails = (paperId: number) => {
    setSelectedPaperId(paperId)
    setIsPaperModalOpen(true)
    fetchPaperDetails(paperId)
  }

  // 논문 모달 닫기
  const handleClosePaperModal = () => {
    setIsPaperModalOpen(false)
    setSelectedPaperId(null)
    setPaperDetails(null)
  }

  // 거절 사유 조회
  const fetchRejectReasons = async (applicationNumber: string) => {
    setIsLoadingRejectReasons(true)
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    try {
      const response = await fetch(`${API_BASE_URL}/api/patents/reject-reasons/${applicationNumber}/`, {
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      })

      if (!response.ok) {
        throw new Error('거절 사유 조회 실패')
      }

      const data = await response.json()

      if (data.has_reject_reasons && data.results) {
        setRejectReasons(data.results)
        setHasRejectData(true)
        setIsRejectModalOpen(true)
      } else {
        setRejectReasons([])
        setHasRejectData(false)
      }

      setIsLoadingRejectReasons(false)
      return data.has_reject_reasons
    } catch (error) {
      console.error('거절 사유 조회 오류:', error)
      setIsLoadingRejectReasons(false)
      setHasRejectData(false)
      return false
    }
  }

  // 거절 사유 모달 닫기
  const handleCloseRejectModal = () => {
    setIsRejectModalOpen(false)
    setRejectReasons([])
  }

  // 의견 제출 통지서 조회
  const fetchOpinionDocuments = async (applicationNumber: string) => {
    setIsLoadingOpinionDocuments(true)
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    try {
      const response = await fetch(`${API_BASE_URL}/api/patents/opinion-documents/${applicationNumber}/`, {
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      })

      if (!response.ok) {
        throw new Error('의견 제출 통지서 조회 실패')
      }

      const data = await response.json()

      if (data.has_opinion_documents && data.results) {
        setOpinionDocuments(data.results)
      } else {
        setOpinionDocuments([])
      }

      setIsLoadingOpinionDocuments(false)
      return data.has_opinion_documents
    } catch (error) {
      console.error('의견 제출 통지서 조회 오류:', error)
      setIsLoadingOpinionDocuments(false)
      setOpinionDocuments([])
      return false
    }
  }


  return (
    <MainLayout>
      <div style={{
        backdropFilter: 'blur(15px)',
        borderTop: '1px solid rgba(229, 231, 235, 0.2)'
      }} className="md:hidden fixed bottom-0 left-0 right-0 flex z-40">
        <button
          onClick={() => setActiveTab("search")}
          className={`flex-1 py-3 text-sm font-medium ${
            activeTab === "search" ? "text-blue-500 border-t-2 border-blue-500" : "text-gray-600"
          }`}
        >
          검색
        </button>
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex-1 py-3 text-sm font-medium ${
            activeTab === "chat" ? "text-blue-500 border-t-2 border-blue-500" : "text-gray-600"
          }`}
        >
          챗봇
        </button>
      </div>

      <div style={{
        position: 'fixed',
        top: '4rem',
        bottom: 0,
        left: 0,
        right: 0,
        display: 'flex'
      }} className="pb-14 md:pb-0">
        {/* Left Panel - Search Area */}
        <div
          style={{
            display: 'flex',
            width: '45%',
            flexDirection: 'column',
            backgroundColor: 'rgba(255, 255, 255, 0.65)',
            backdropFilter: 'blur(15px)',
            borderRight: '1px solid rgba(209, 213, 219, 0.2)'
          }}
          className={`${activeTab === "search" ? "flex" : "hidden"} md:flex md:w-[45%] lg:w-[40%]`}
        >
          <div style={{
            flexShrink: 0,
            borderBottom: '1px solid rgba(209, 213, 219, 0.5)',
            maxHeight: '384px',
            overflowY: 'auto'
          }}>
            <div className="p-6">
              {/* Search Type Tabs */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setSearchType("patent")}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                    searchType === "patent"
                      ? "bg-[#3B82F6] text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  특허 검색
                </button>
                <button
                  onClick={() => setSearchType("paper")}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                    searchType === "paper"
                      ? "bg-[#3B82F6] text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  논문 검색
                </button>
              </div>

              <div className="flex gap-2">
                <Input
                  type="text"
                  placeholder={searchType === "patent" ? "특허 키워드 입력 (예: 인공지능, 반도체)" : "논문 키워드 입력 (예: machine learning, AI)"}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="flex-1 rounded-lg p-3"
                />
                <Button
                  onClick={handleSearch}
                  disabled={isSearching}
                  className="bg-[#3B82F6] hover:bg-[#2563EB] px-4 flex-shrink-0"
                >
                  {isSearching ? <Loader2 className="h-5 w-5 animate-spin" /> : <Search className="h-5 w-5" />}
                </Button>
              </div>

              <div className="flex flex-wrap gap-4 mt-3">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="title"
                    checked={searchInTitle}
                    onCheckedChange={(checked) => setSearchInTitle(checked as boolean)}
                  />
                  <label htmlFor="title" className="text-sm cursor-pointer">
                    제목에서 검색
                  </label>
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="summary"
                    checked={searchInSummary}
                    onCheckedChange={(checked) => setSearchInSummary(checked as boolean)}
                  />
                  <label htmlFor="summary" className="text-sm cursor-pointer">
                    {searchType === "patent" ? "요약에서 검색" : "초록에서 검색"}
                  </label>
                </div>
                {searchType === "patent" && (
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="claims"
                      checked={searchInClaims}
                      onCheckedChange={(checked) => setSearchInClaims(checked as boolean)}
                    />
                    <label htmlFor="claims" className="text-sm cursor-pointer">
                      청구항에서 검색
                    </label>
                  </div>
                )}
              </div>

              <div className="mt-4">
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center justify-between w-full text-sm font-medium text-gray-700 hover:text-gray-900"
                >
                  <span>고급 필터</span>
                  {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>

                {showAdvanced && (
                  <div className="mt-3 space-y-3">
                    {searchType === "patent" ? (
                      <>
                        <div>
                          <label className="text-xs text-gray-600 mb-1 block">IPC/CPC 코드</label>
                          <Input
                            type="text"
                            placeholder="A01B"
                            value={ipcCode}
                            onChange={(e) => setIpcCode(e.target.value)}
                            className="text-sm"
                          />
                        </div>

                        <div>
                          <label className="text-xs text-gray-600 mb-1 block">출원일 범위</label>
                          <div className="flex items-center gap-2">
                            <Input
                              type="date"
                              value={applicationStartDate}
                              onChange={(e) => setApplicationStartDate(e.target.value)}
                              className="text-sm"
                            />
                            <span className="text-gray-500">~</span>
                            <Input
                              type="date"
                              value={applicationEndDate}
                              onChange={(e) => setApplicationEndDate(e.target.value)}
                              className="text-sm"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="text-xs text-gray-600 mb-1 block">공개일 범위</label>
                          <div className="flex items-center gap-2">
                            <Input
                              type="date"
                              value={publicationStartDate}
                              onChange={(e) => setPublicationStartDate(e.target.value)}
                              className="text-sm"
                            />
                            <span className="text-gray-500">~</span>
                            <Input
                              type="date"
                              value={publicationEndDate}
                              onChange={(e) => setPublicationEndDate(e.target.value)}
                              className="text-sm"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="text-xs text-gray-600 mb-1 block">법적상태</label>
                          <select
                            value={legalStatusFilter}
                            onChange={(e) => setLegalStatusFilter(e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="">전체</option>
                            <option value="등록">등록</option>
                            <option value="공개">공개</option>
                            <option value="거절">거절</option>
                            <option value="취하">취하</option>
                            <option value="포기">포기</option>
                            <option value="소멸">소멸</option>
                          </select>
                        </div>
                      </>
                    ) : (
                      <div>
                        <label className="text-xs text-gray-600 mb-1 block">발행일 범위</label>
                        <div className="flex items-center gap-2">
                          <Input
                            type="date"
                            value={applicationStartDate}
                            onChange={(e) => setApplicationStartDate(e.target.value)}
                            className="text-sm"
                          />
                          <span className="text-gray-500">~</span>
                          <Input
                            type="date"
                            value={applicationEndDate}
                            onChange={(e) => setApplicationEndDate(e.target.value)}
                            className="text-sm"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 검색 전/결과 없음 상태 */}
          {(!hasSearched || searchResults.length === 0) && (
            <div style={{ flex: 1, overflowY: 'auto' }}>
              {!hasSearched && !isSearching && (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-gray-500">
                    <Search className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                    <p className="text-sm">
                      키워드를 입력하여 {searchType === "patent" ? "특허" : "논문"}를 검색하세요
                    </p>
                  </div>
                </div>
              )}

              {hasSearched && searchResults.length === 0 && (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                    <p className="text-sm">검색 결과가 없습니다</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 검색 결과 있음 */}
          {hasSearched && searchResults.length > 0 && (
            <>
              {isUserSearched && (
                <div style={{
                  flexShrink: 0,
                  padding: '1rem',
                  backgroundColor: 'rgba(249, 250, 251, 0.3)',
                  borderBottom: '1px solid rgba(229, 231, 235, 0.2)'
                }}>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                      {searchType === "patent" ? "특허" : "논문"} 총 {totalCount.toLocaleString()}건 검색됨
                    </p>
                    <select
                      value={sortBy}
                      onChange={(e) => {
                        const newSortBy = e.target.value
                        setSortBy(newSortBy)
                        fetchPatents(searchQuery, 1, newSortBy)
                      }}
                      className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                    >
                      <option value="date_desc">최신순</option>
                      <option value="date_asc">오래된순</option>
                    </select>
                  </div>
                </div>
              )}

              <div style={{ flex: 1, overflowY: 'auto' }}>
                {searchResults.length === 0 && !isSearching ? (
                  <div className="flex flex-col items-center justify-center h-full py-12 px-4">
                    <div className="text-gray-400 mb-4">
                      <svg className="w-24 h-24 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-700 mb-2">검색 결과가 없습니다</h3>
                    <p className="text-gray-500 text-center max-w-md">
                      {searchQuery ? (
                        <>
                          '<span className="font-semibold">{searchQuery}</span>'에 대한 검색 결과를 찾을 수 없습니다.<br />
                          다른 검색어를 입력하거나 필터 조건을 변경해보세요.
                        </>
                      ) : (
                        <>검색어를 입력하거나 필터를 선택해주세요.</>
                      )}
                    </p>
                  </div>
                ) : (
                  searchResults.map((patent) => (
                    <div
                      key={patent.id}
                      className={`p-4 border-b border-gray-200 hover:bg-gray-50 transition-colors ${
                        patent.highlight ? "bg-yellow-100 animate-pulse" : ""
                      }`}
                    >
                    <div
                      onClick={searchType === "patent" ? () => handleViewDetails(patent.id) : () => handleViewPaperDetails(patent.id)}
                      className="cursor-pointer"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="text-base font-semibold flex-1">{patent.title}</h3>
                        {searchType === "patent" && patent.legalStatus && (
                          <div className="ml-2 flex-shrink-0">
                            {getLegalStatusBadge(patent.legalStatus)}
                          </div>
                        )}
                      </div>

                      <div className="text-xs text-gray-500 mb-2">
                        {searchType === "patent" ? (
                          <>
                            <span>출원번호: {patent.applicationNumber}</span>
                            {patent.applicationDate && (
                              <>
                                <span className="mx-2">•</span>
                                <span>출원일: {patent.applicationDate}</span>
                              </>
                            )}
                          </>
                        ) : (
                          <>
                            <span>저자: {patent.applicationNumber}</span>
                            {patent.applicationDate && (
                              <>
                                <span className="mx-2">•</span>
                                <span>발행일: {patent.applicationDate}</span>
                              </>
                            )}
                          </>
                        )}
                      </div>

                      <p className="text-sm text-gray-700 line-clamp-3">
                        {patent.summary}
                      </p>
                    </div>

                    {searchType === "paper" && patent.pdfLink && (
                      <div className="mt-3">
                        <Button
                          onClick={() => window.open(patent.pdfLink, '_blank')}
                          className="bg-[#3B82F6] hover:bg-[#2563EB] text-white text-sm"
                          size="sm"
                        >
                          <FileText className="h-4 w-4 mr-2" />
                          PDF 보기
                        </Button>
                      </div>
                    )}
                  </div>
                  ))
                )}
              </div>

              <div style={{
                flexShrink: 0,
                padding: '0.75rem',
                borderTop: '1px solid rgba(229, 231, 235, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.25rem',
                flexWrap: 'wrap'
              }}>
                {/* 처음 버튼: 첫 페이지로 이동 */}
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === 1 || totalPages === 0}
                  onClick={() => handlePageChange(1)}
                  style={{ minWidth: '50px' }}
                >
                  처음
                </Button>

                {/* 이전 버튼: 5개 묶음씩 이동 */}
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === 1 || totalPages === 0}
                  onClick={() => {
                    const maxPagesToShow = 5
                    const currentGroup = Math.floor((currentPage - 1) / maxPagesToShow)
                    const prevGroupFirstPage = Math.max(1, currentGroup * maxPagesToShow)
                    handlePageChange(prevGroupFirstPage)
                  }}
                  style={{ minWidth: '50px' }}
                >
                  이전
                </Button>

                {/* 페이지 번호 버튼 */}
                {(() => {
                  const maxPagesToShow = 5
                  const pages = []

                  if (totalPages === 0) return pages

                  // 현재 페이지 그룹 계산
                  const currentGroup = Math.floor((currentPage - 1) / maxPagesToShow)
                  let startPage = currentGroup * maxPagesToShow + 1
                  let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1)

                  for (let i = startPage; i <= endPage; i++) {
                    const isFirstInGroup = i === startPage
                    const isLastInGroup = i === endPage

                    pages.push(
                      <Button
                        key={i}
                        variant={currentPage === i ? "default" : "outline"}
                        size="sm"
                        onClick={() => {
                          // 첫 번째 페이지 번호 클릭: 이전 그룹으로
                          if (isFirstInGroup && startPage > 1) {
                            const prevGroupLastPage = startPage - 1
                            handlePageChange(prevGroupLastPage)
                          }
                          // 마지막 페이지 번호 클릭: 다음 그룹으로
                          else if (isLastInGroup && endPage < totalPages) {
                            const nextGroupFirstPage = endPage + 1
                            handlePageChange(nextGroupFirstPage)
                          }
                          // 중간 페이지 번호: 해당 페이지로 이동
                          else {
                            handlePageChange(i)
                          }
                        }}
                        className={currentPage === i ? "bg-[#3B82F6]" : ""}
                        style={{ minWidth: '40px', padding: '0 10px' }}
                      >
                        {i}
                      </Button>
                    )
                  }

                  return pages
                })()}

                {/* 다음 버튼: 5개 묶음씩 이동 */}
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === totalPages || totalPages === 0}
                  onClick={() => {
                    const maxPagesToShow = 5
                    const currentGroup = Math.floor((currentPage - 1) / maxPagesToShow)
                    const nextGroupFirstPage = Math.min(totalPages, (currentGroup + 1) * maxPagesToShow + 1)
                    handlePageChange(nextGroupFirstPage)
                  }}
                  style={{ minWidth: '50px' }}
                >
                  다음
                </Button>

                {/* 끝 버튼: 마지막 페이지로 이동 */}
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === totalPages || totalPages === 0}
                  onClick={() => handlePageChange(totalPages)}
                  style={{ minWidth: '50px' }}
                >
                  끝
                </Button>
              </div>
            </>
          )}
        </div>

        {/* Right Panel - Chatbot Area */}
        <div
          style={{
            display: 'flex',
            width: '55%',
            backgroundColor: 'rgba(255, 255, 255, 0.65)',
            backdropFilter: 'blur(15px)',
            flexDirection: 'column',
            position: 'relative'
          }}
          className={`${activeTab === "chat" ? "flex" : "hidden"} md:flex md:w-[55%] lg:w-[60%]`}
        >
          <div style={{
            height: '3rem',
            borderBottom: '1px solid rgba(229, 231, 235, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 1rem'
          }}>
            <h2 className="text-lg font-semibold text-gray-800">AI 챗봇</h2>
            <Button
              onClick={startNewChat}
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
            >
              <span className="text-lg">+</span>
              새 채팅
            </Button>
          </div>

          <div
            ref={messagesContainerRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '1.5rem',
              minHeight: 0
            }}
            className="space-y-4 scroll-smooth"
          >
            {messages.map((message) => {
              if (message.type === "system") {
                return (
                  <div key={message.id} className="flex justify-center">
                    <div className="bg-gray-200 text-gray-700 text-xs rounded-lg px-3 py-2 whitespace-pre-line">
                      {message.content}
                    </div>
                  </div>
                )
              }

              if (message.type === "user") {
                return (
                  <div key={message.id} className="flex justify-end">
                    <div className="bg-[#3B82F6] text-white rounded-2xl px-4 py-3 max-w-[70%]">
                      <p className="whitespace-pre-wrap break-words" style={{ lineHeight: '1.6', wordBreak: 'break-word' }}>
                        {message.content}
                      </p>
                      {message.file && (
                        <div className="mt-2 flex items-center gap-2 bg-blue-600 rounded-lg px-3 py-2">
                          <Paperclip className="h-4 w-4" />
                          <div className="text-xs">
                            <p className="font-semibold">{message.file.name}</p>
                            <p className="opacity-80">{(message.file.size / 1024).toFixed(1)} KB</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )
              }

              return (
                <div key={message.id} className="flex justify-start">
                  <div className="bg-gray-100 text-gray-800 rounded-2xl px-4 py-3 max-w-[70%]">
                    <div
                      className="whitespace-pre-wrap break-words"
                      style={{
                        lineHeight: '1.6',
                        wordBreak: 'break-word'
                      }}
                    >
                      {message.content.split('\n').map((line, idx) => {
                        // 리스트 항목 처리 (-, *, 1., 2. 등)
                        if (line.match(/^[\s]*[-*•]\s/)) {
                          return (
                            <div key={idx} className="flex gap-2 mb-1">
                              <span className="text-blue-600">•</span>
                              <span className="flex-1">{line.replace(/^[\s]*[-*•]\s/, '')}</span>
                            </div>
                          )
                        }
                        // 번호 리스트 처리
                        if (line.match(/^[\s]*\d+\.\s/)) {
                          const num = line.match(/^[\s]*(\d+)\.\s/)
                          return (
                            <div key={idx} className="flex gap-2 mb-1">
                              <span className="text-blue-600 font-semibold">{num?.[1]}.</span>
                              <span className="flex-1">{line.replace(/^[\s]*\d+\.\s/, '')}</span>
                            </div>
                          )
                        }
                        // 헤더 처리 (## 또는 ** 로 감싸진 텍스트)
                        if (line.match(/^##\s/)) {
                          return (
                            <div key={idx} className="font-bold text-gray-900 mt-2 mb-1">
                              {line.replace(/^##\s/, '')}
                            </div>
                          )
                        }
                        // 일반 텍스트
                        return line ? (
                          <div key={idx} className="mb-1">{line}</div>
                        ) : (
                          <div key={idx} className="h-2" />
                        )
                      })}
                    </div>
                  </div>
                </div>
              )
            })}

            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-800 rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                  </div>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          <div style={{
            flexShrink: 0,
            padding: '1rem',
            borderTop: '1px solid rgba(229, 231, 235, 0.2)'
          }}>
            {uploadedFile && (
              <div className="mb-3 flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
                <Paperclip className="h-4 w-4 text-blue-600" />
                <div className="flex-1 text-sm">
                  <p className="font-semibold text-blue-900">{uploadedFile.name}</p>
                  <p className="text-xs text-blue-700">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
                </div>
                <button
                  onClick={() => setUploadedFile(null)}
                  className="p-1 hover:bg-blue-100 rounded transition-colors"
                >
                  <X className="h-4 w-4 text-blue-600" />
                </button>
              </div>
            )}

            <div className="relative">
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileUpload}
                className="hidden"
                accept=".pdf,.doc,.docx,.txt"
              />
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    handleSendMessage()
                  }
                }}
                placeholder="메시지를 입력하세요... (파일 업로드도 가능합니다)"
                rows={2}
                className="w-full border border-gray-300 rounded-lg p-3 pr-20 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="absolute bottom-3 right-3 flex gap-1">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-full p-2 transition-colors"
                  title="파일 업로드"
                >
                  <Paperclip className="h-4 w-4" />
                </button>
                <button
                  onClick={handleSendMessage}
                  className="bg-[#3B82F6] hover:bg-[#2563EB] text-white rounded-full p-2 transition-colors"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Patent Detail Modal */}
      {isModalOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={handleCloseModal}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">특허 상세 정보</h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="px-6 py-4">
              {isLoadingDetails ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                  <span className="ml-3 text-gray-600">불러오는 중...</span>
                </div>
              ) : patentDetails ? (
                <div className="space-y-6">
                  {/* 발명의 명칭 */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">발명의 명칭</h3>
                    <p className="text-gray-800">{patentDetails.title}</p>
                  </div>

                  {/* 출원 정보 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-1">출원번호</h3>
                      <p className="text-gray-800">{patentDetails.applicationNumber}</p>
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-1">출원일</h3>
                      <p className="text-gray-800">{patentDetails.applicationDate || '-'}</p>
                    </div>
                    {patentDetails.applicant && (
                      <div>
                        <h3 className="text-sm font-semibold text-gray-700 mb-1">출원인</h3>
                        <p className="text-gray-800">{patentDetails.applicant}</p>
                      </div>
                    )}
                    {patentDetails.registrationNumber && (
                      <div>
                        <h3 className="text-sm font-semibold text-gray-700 mb-1">등록번호</h3>
                        <p className="text-gray-800">{patentDetails.registrationNumber}</p>
                      </div>
                    )}
                    {patentDetails.registrationDate && (
                      <div>
                        <h3 className="text-sm font-semibold text-gray-700 mb-1">등록일</h3>
                        <p className="text-gray-800">{patentDetails.registrationDate}</p>
                      </div>
                    )}
                  </div>

                  {/* 분류 코드 */}
                  {(patentDetails.ipcCode || patentDetails.cpcCode) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {patentDetails.ipcCode && (
                        <div>
                          <h3 className="text-sm font-semibold text-gray-700 mb-1">IPC 분류</h3>
                          <p className="text-gray-800 text-sm">{patentDetails.ipcCode}</p>
                        </div>
                      )}
                      {patentDetails.cpcCode && (
                        <div>
                          <h3 className="text-sm font-semibold text-gray-700 mb-1">CPC 분류</h3>
                          <p className="text-gray-800 text-sm">{patentDetails.cpcCode}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* 요약 */}
                  {patentDetails.summary && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">요약</h3>
                      <p className="text-gray-800 whitespace-pre-line leading-relaxed">
                        {patentDetails.summary}
                      </p>
                    </div>
                  )}

                  {/* 청구항 */}
                  {patentDetails.claims && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">청구항</h3>
                      <div className="text-gray-800 leading-relaxed space-y-4">
                        {patentDetails.claims.split(/(?=\[청구항\s*\d+\]|\【청구항\s*\d+\】|청구항\s*\d+[\.\:)])/g).map((claim, index) => {
                          const trimmedClaim = claim.trim()
                          if (!trimmedClaim) return null

                          // 청구항 번호와 내용 분리
                          const claimMatch = trimmedClaim.match(/^(\[청구항\s*\d+\]|\【청구항\s*\d+\】|청구항\s*\d+[\.\:)])(.+)$/s)

                          if (claimMatch) {
                            const [, claimNumber, claimContent] = claimMatch
                            return (
                              <div key={index} className="border-l-2 border-blue-200 pl-4 py-2">
                                <div className="font-semibold text-blue-700 mb-2">{claimNumber}</div>
                                <div className="whitespace-pre-line">{claimContent.trim()}</div>
                              </div>
                            )
                          }

                          return (
                            <div key={index} className="whitespace-pre-line">
                              {trimmedClaim}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center py-12">
                  <p className="text-gray-600">상세 정보를 불러올 수 없습니다.</p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={handleCloseModal}
              >
                닫기
              </Button>
              {patentDetails && hasRejectData && (
                <Button
                  onClick={async () => {
                    await Promise.all([
                      fetchRejectReasons(patentDetails.applicationNumber),
                      fetchOpinionDocuments(patentDetails.applicationNumber)
                    ])
                  }}
                  disabled={isLoadingRejectReasons || isLoadingOpinionDocuments}
                  className="bg-[#3B82F6] hover:bg-[#2563EB]"
                >
                  {(isLoadingRejectReasons || isLoadingOpinionDocuments) ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <FileText className="h-4 w-4 mr-2" />
                  )}
                  거절 내역 확인
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Paper Detail Modal */}
      {isPaperModalOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={handleClosePaperModal}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">논문 상세 정보</h2>
              <button
                onClick={handleClosePaperModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="px-6 py-4">
              {isLoadingPaperDetails ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                  <span className="ml-3 text-gray-600">불러오는 중...</span>
                </div>
              ) : paperDetails ? (
                <div className="space-y-6">
                  {/* 논문 제목 */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">논문 제목</h3>
                    <p className="text-gray-800 text-lg">{paperDetails.title_kr}</p>
                    {paperDetails.title_en && (
                      <p className="text-gray-600 text-sm mt-2 italic">{paperDetails.title_en}</p>
                    )}
                  </div>

                  {/* 저자 정보 */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-1">저자</h3>
                    <p className="text-gray-800">{paperDetails.authors}</p>
                  </div>

                  {/* 초록 (한글) */}
                  {paperDetails.abstract_kr && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">초록</h3>
                      <p className="text-gray-800 whitespace-pre-line leading-relaxed">
                        {paperDetails.abstract_kr}
                      </p>
                    </div>
                  )}

                  {/* 초록 (영문) */}
                  {paperDetails.abstract_en && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Abstract (영문)</h3>
                      <p className="text-gray-700 whitespace-pre-line leading-relaxed text-sm">
                        {paperDetails.abstract_en}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center py-12">
                  <p className="text-gray-600">상세 정보를 불러올 수 없습니다.</p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={handleClosePaperModal}
              >
                닫기
              </Button>
              {paperDetails && paperDetails.pdf_link && (
                <Button
                  onClick={() => window.open(paperDetails.pdf_link, '_blank')}
                  className="bg-[#3B82F6] hover:bg-[#2563EB]"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  PDF 보기
                </Button>
              )}
              {paperDetails && paperDetails.abstract_page_link && (
                <Button
                  onClick={() => window.open(paperDetails.abstract_page_link, '_blank')}
                  className="bg-[#10B981] hover:bg-[#059669]"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  논문 페이지 보기
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Reject Reason Modal */}
      {isRejectModalOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={handleCloseRejectModal}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">거절 내역</h2>
              <button
                onClick={handleCloseRejectModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200">
              <div className="flex">
                <button
                  onClick={() => setRejectDocumentTab("specification")}
                  className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                    rejectDocumentTab === "specification"
                      ? "text-[#3B82F6] border-b-2 border-[#3B82F6] bg-blue-50"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  특허 거절 결정서
                </button>
                <button
                  onClick={() => setRejectDocumentTab("opinion")}
                  className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                    rejectDocumentTab === "opinion"
                      ? "text-[#3B82F6] border-b-2 border-[#3B82F6] bg-blue-50"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  의견 제출 통지서
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="px-6 py-4 overflow-y-auto flex-1">
              {rejectDocumentTab === "specification" ? (
                // 특허 거절 결정서 탭
                rejectReasons.length > 0 ? (
                  <div className="space-y-6">
                    {rejectReasons.map((reason, index) => (
                      <div key={reason.id} className="border-b border-gray-200 pb-6 last:border-b-0">
                        {/* 거절 문서 정보 */}
                        <div className="bg-gray-50 rounded-lg p-4 mb-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                            <div>
                              <span className="font-semibold text-gray-700">발송일자:</span>
                              <span className="ml-2 text-gray-600">{reason.send_date}</span>
                            </div>
                            <div>
                              <span className="font-semibold text-gray-700">발송번호:</span>
                              <span className="ml-2 text-gray-600">{reason.send_number}</span>
                            </div>
                            <div>
                              <span className="font-semibold text-gray-700">출원인:</span>
                              <span className="ml-2 text-gray-600">{reason.applicant}</span>
                            </div>
                            {reason.agent && (
                              <div>
                                <span className="font-semibold text-gray-700">대리인:</span>
                                <span className="ml-2 text-gray-600">{reason.agent}</span>
                              </div>
                            )}
                            <div>
                              <span className="font-semibold text-gray-700">심사기관:</span>
                              <span className="ml-2 text-gray-600">{reason.examination_office}</span>
                            </div>
                            <div>
                              <span className="font-semibold text-gray-700">심사관:</span>
                              <span className="ml-2 text-gray-600">{reason.examiner}</span>
                            </div>
                          </div>
                        </div>

                        {/* 거절 결정서 내용 */}
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-3">
                            특허 거절 결정서 내용{rejectReasons.length > 1 ? ` ${index + 1}` : ''}
                          </h3>
                          <div className="bg-white border border-gray-200 rounded-lg p-4">
                            <p className="text-gray-800 whitespace-pre-line leading-relaxed">
                              {reason.processed_text || "특허 거절 결정서 내용이 없습니다."}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-12">
                    <p className="text-gray-600">특허 거절 결정서가 없습니다.</p>
                  </div>
                )
              ) : (
                // 의견 제출 통지서 탭
                isLoadingOpinionDocuments ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-[#3B82F6]" />
                  </div>
                ) : opinionDocuments.length > 0 ? (
                  <div className="space-y-6">
                    {opinionDocuments.map((opinion, index) => (
                      <div key={opinion.id} className="border-b border-gray-200 pb-6 last:border-b-0">
                        {/* 의견 제출 통지서 내용 */}
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-3">
                            의견 제출 통지서 내용{opinionDocuments.length > 1 ? ` ${index + 1}` : ''}
                          </h3>
                          <div className="bg-white border border-gray-200 rounded-lg p-4">
                            <p className="text-gray-800 whitespace-pre-line leading-relaxed">
                              {opinion.full_text || "의견 제출 통지서 내용이 없습니다."}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-12">
                    <p className="text-gray-600">의견 제출 통지서가 없습니다.</p>
                  </div>
                )
              )}
            </div>

            {/* Modal Footer */}
            <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end">
              <Button
                variant="outline"
                onClick={handleCloseRejectModal}
              >
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  )
}
