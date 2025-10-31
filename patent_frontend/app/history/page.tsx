"use client"
import { API_BASE_URL } from "@/lib/config"

import { MainLayout } from "@/components/main-layout"
import { Search, Users, Trash2 } from "lucide-react"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"


interface ChatConversation {
  id: string
  title: string
  user_name: string
  user_id: string
  created_at: string
  updated_at: string
  message_count: number
  last_message: {
    content: string
    type: string
    created_at: string
  } | null
}

export default function HistoryPage() {
  const router = useRouter()
  const [sharedConversations, setSharedConversations] = useState<ChatConversation[]>([])
  const [myConversations, setMyConversations] = useState<ChatConversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [currentUser, setCurrentUser] = useState<any>(null)

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("user") || "{}")
    setCurrentUser(user)
    loadHistory()
  }, [])

  const handleConversationClick = (conversationId: string) => {
    // conversation_id를 URL 파라미터로 전달하여 검색 페이지로 이동
    router.push(`/search?conversation_id=${conversationId}&tab=chat`)
  }

  const loadHistory = async () => {
    setLoading(true)
    const token = localStorage.getItem("access_token")

    try {
      // 부서 공유 챗봇 대화 (같은 부서의 모든 사용자 대화)
      const sharedRes = await fetch(`${API_BASE_URL}/api/chatbot/conversations/?my=false`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (sharedRes.ok) {
        const data = await sharedRes.json()
        setSharedConversations(data)
      }

      // 내 챗봇 대화
      const myRes = await fetch(`${API_BASE_URL}/api/chatbot/conversations/?my=true`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (myRes.ok) {
        const data = await myRes.json()
        setMyConversations(data)
      }
    } catch (err) {
      setError("대화 기록을 불러오는데 실패했습니다.")
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteConversation = async (conversationId: string) => {
    if (!confirm("정말 삭제하시겠습니까?")) return

    const token = localStorage.getItem("access_token")
    setError("")
    setSuccess("")

    try {
      const response = await fetch(`${API_BASE_URL}/api/chatbot/conversations/${conversationId}/`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })

      if (response.ok) {
        setSuccess("대화가 삭제되었습니다.")
        loadHistory()
      } else {
        const data = await response.json()
        setError(data.error || "삭제에 실패했습니다.")
      }
    } catch (err) {
      setError("서버 연결에 실패했습니다.")
    }
  }

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">로딩 중...</p>
          </div>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="h-[calc(100vh-4rem)] bg-gray-50 overflow-y-auto">
        <div className="p-6 max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">챗봇 대화 기록</h1>
              <p className="text-gray-600 mt-1">부서 공유 및 개인 챗봇 대화를 확인합니다</p>
            </div>
            <Button onClick={loadHistory} variant="outline">
              새로고침
            </Button>
          </div>

          {/* Alerts */}
          {error && (
            <Alert className="bg-red-50 border-red-200">
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </Alert>
          )}
          {success && (
            <Alert className="bg-green-50 border-green-200">
              <AlertDescription className="text-green-800">{success}</AlertDescription>
            </Alert>
          )}

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">부서 공유 대화</p>
                  <p className="text-2xl font-bold">{sharedConversations.length}개</p>
                </div>
                <Users className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">내 대화</p>
                  <p className="text-2xl font-bold">{myConversations.length}개</p>
                </div>
                <Search className="h-8 w-8 text-green-600" />
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">총 채팅 수</p>
                  <p className="text-2xl font-bold">
                    {sharedConversations.length + myConversations.length}개
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    부서 {sharedConversations.length}개 · 개인 {myConversations.length}개
                  </p>
                </div>
                <Search className="h-8 w-8 text-orange-600" />
              </div>
            </div>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="shared" className="space-y-4">
            <TabsList>
              <TabsTrigger value="shared">부서 공유 대화</TabsTrigger>
              <TabsTrigger value="my">내 대화 기록</TabsTrigger>
            </TabsList>

            {/* 부서 공유 탭 */}
            <TabsContent value="shared">
              <div className="bg-white rounded-lg shadow">
                {sharedConversations.length === 0 ? (
                  <p className="text-center text-gray-500 py-12">공유된 대화가 없습니다.</p>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          대화 제목
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          작성자
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          마지막 메시지
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          날짜
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {sharedConversations.map((conv) => (
                        <tr
                          key={conv.id}
                          className="hover:bg-gray-50 cursor-pointer"
                          onClick={() => handleConversationClick(conv.id)}
                        >
                          <td className="px-4 py-4 text-sm font-medium">{conv.title}</td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {conv.user_name}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600 max-w-xs truncate">
                            {conv.last_message ? conv.last_message.content : '-'}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {new Date(conv.updated_at).toLocaleString("ko-KR")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </TabsContent>

            {/* 내 대화 기록 탭 */}
            <TabsContent value="my">
              <div className="bg-white rounded-lg shadow">
                {myConversations.length === 0 ? (
                  <p className="text-center text-gray-500 py-12">내 대화 기록이 없습니다.</p>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          대화 제목
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          마지막 메시지
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          날짜
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          작업
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {myConversations.map((conv) => (
                        <tr
                          key={conv.id}
                          className="hover:bg-gray-50 cursor-pointer"
                          onClick={() => handleConversationClick(conv.id)}
                        >
                          <td className="px-4 py-4 text-sm font-medium">{conv.title}</td>
                          <td className="px-4 py-4 text-sm text-gray-600 max-w-xs truncate">
                            {conv.last_message ? conv.last_message.content : '-'}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {new Date(conv.updated_at).toLocaleString("ko-KR")}
                          </td>
                          <td className="px-4 py-4 text-sm">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDeleteConversation(conv.id)
                              }}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </MainLayout>
  )
}
