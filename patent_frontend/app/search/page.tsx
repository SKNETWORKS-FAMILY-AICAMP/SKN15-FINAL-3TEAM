"use client"

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
  highlight?: boolean
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

function highlightText(text: string, keyword: string) {
  if (!keyword) return text
  const parts = text.split(new RegExp(`(${keyword})`, "gi"))
  return parts.map((part, i) =>
    part.toLowerCase() === keyword.toLowerCase() ? (
      <mark key={i} className="bg-yellow-200">
        {part}
      </mark>
    ) : (
      part
    ),
  )
}

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState("인공지능")
  const [searchInTitle, setSearchInTitle] = useState(true)
  const [searchInSummary, setSearchInSummary] = useState(true)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [ipcCode, setIpcCode] = useState("")
  const [applicationStartDate, setApplicationStartDate] = useState("")
  const [applicationEndDate, setApplicationEndDate] = useState("")
  const [publicationStartDate, setPublicationStartDate] = useState("")
  const [publicationEndDate, setPublicationEndDate] = useState("")
  const [sortBy, setSortBy] = useState("latest")
  const [currentPage, setCurrentPage] = useState(1)
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES)
  const [inputMessage, setInputMessage] = useState("")
  const [searchResults, setSearchResults] = useState<Patent[]>(SAMPLE_PATENTS)
  const [isSearching, setIsSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(true)
  const [isTyping, setIsTyping] = useState(false)
  const [activeTab, setActiveTab] = useState<"search" | "chat">("search")
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

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

  const handleSearch = () => {
    setIsSearching(true)
    setHasSearched(false)

    setTimeout(() => {
      setIsSearching(false)
      setHasSearched(true)
      setSearchResults(SAMPLE_PATENTS)
    }, 1000)
  }


  return (
    <MainLayout>
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex z-40">
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

      <div className="h-[calc(100vh-4rem)] md:h-[calc(100vh-4rem)] flex pb-14 md:pb-0">
        {/* Left Panel - Search Area */}
          <div
        className={`${
          activeTab === "search" ? "block" : "hidden"
        } md:block w-full md:w-[45%] lg:w-[40%] border-r border-[#D1D5DB] flex flex-col`}
      >
          <div className="flex-shrink-0 border-b border-[#D1D5DB]">
            <div className="p-6">
              <div className="flex gap-2">
                <Input
                  type="text"
                  placeholder="특허 키워드 입력 (예: 인공지능, 반도체)"
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

              <div className="flex gap-4 mt-3">
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
                    요약에서 검색
                  </label>
                </div>
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
                      <label className="text-xs text-gray-600 mb-1 block">정렬 방식</label>
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="latest">최신순</option>
                        <option value="relevance">관련도순</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {!hasSearched && !isSearching && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-gray-500">
                  <Search className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                  <p className="text-sm">키워드를 입력하여 특허를 검색하세요</p>
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

            {hasSearched && searchResults.length > 0 && (
              <>
                <div className="p-4 bg-gray-50">
                  <p className="text-sm text-gray-600">총 143건 검색됨</p>
                </div>

                <div className="max-h-[calc(3*200px)] overflow-y-auto">
                  {searchResults.map((patent) => (
                    <div
                      key={patent.id}
                      className={`p-4 border-b border-gray-200 hover:bg-gray-50 transition-colors min-h-[200px] ${
                        patent.highlight ? "bg-yellow-100 animate-pulse" : ""
                      }`}
                    >
                      <h3 className="text-base font-semibold mb-1">{highlightText(patent.title, searchQuery)}</h3>

                      <div className="text-xs text-gray-500 mb-2">
                        <span>출원번호: {patent.applicationNumber}</span>
                        <span className="mx-2">•</span>
                        <span>출원일: {patent.applicationDate}</span>
                      </div>

                      <p className="text-sm text-gray-700 line-clamp-2 mb-3">
                        {highlightText(patent.summary, searchQuery)}
                      </p>

                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSendToChat(patent)}
                          className="flex items-center gap-1 text-sm text-[#3B82F6] hover:text-[#2563EB]"
                        >
                          <Send className="h-4 w-4" />
                          챗봇에 전송
                        </button>
                        <button className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
                          <FileText className="h-4 w-4" />
                          상세보기
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-4 border-t border-gray-200 flex items-center justify-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(currentPage - 1)}
                  >
                    이전
                  </Button>
                  {[1, 2, 3, 4, 5].map((page) => (
                    <Button
                      key={page}
                      variant={currentPage === page ? "default" : "outline"}
                      size="sm"
                      onClick={() => setCurrentPage(page)}
                      className={currentPage === page ? "bg-[#3B82F6]" : ""}
                    >
                      {page}
                    </Button>
                  ))}
                  <span className="text-sm text-gray-500">...</span>
                  <Button variant="outline" size="sm">
                    10
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setCurrentPage(currentPage + 1)}>
                    다음
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Right Panel - Chatbot Area */}
        <div
          className={`${
            activeTab === "chat" ? "block" : "hidden"
          } md:block w-full md:w-[55%] lg:w-[60%] bg-white flex flex-col relative`}
        >
          <div className="h-12 border-b border-gray-200 flex items-center justify-between px-4">
            <h2 className="text-lg font-semibold text-gray-800">AI 챗봇</h2>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-4">
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
                      <p>{message.content}</p>
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
                    <p>{message.content}</p>
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

          <div className="flex-shrink-0 p-4 border-t border-gray-200">
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
    </MainLayout>
  )
}
