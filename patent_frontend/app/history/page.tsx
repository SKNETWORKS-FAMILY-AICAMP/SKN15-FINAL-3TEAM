"use client"

import { MainLayout } from "@/components/main-layout"
import { Search, Users, Trash2, User } from "lucide-react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface SearchHistory {
  history_id: string
  query: string
  search_type: string
  search_type_display: string
  results_count: number
  created_by_name: string
  created_at: string
  company_name: string
  department_name: string
  is_shared: boolean
}

export default function HistoryPage() {
  const [sharedHistory, setSharedHistory] = useState<SearchHistory[]>([])
  const [myHistory, setMyHistory] = useState<SearchHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    setLoading(true)
    const token = localStorage.getItem("access_token")

    try {
      // 공유 히스토리 (부서 전체)
      const sharedRes = await fetch(`${API_BASE_URL}/api/accounts/history/?shared=true`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (sharedRes.ok) {
        const data = await sharedRes.json()
        setSharedHistory(data)
      }

      // 내 히스토리만
      const myRes = await fetch(`${API_BASE_URL}/api/accounts/history/?my=true`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (myRes.ok) {
        const data = await myRes.json()
        setMyHistory(data)
      }
    } catch (err) {
      setError("히스토리를 불러오는데 실패했습니다.")
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (historyId: string) => {
    if (!confirm("정말 삭제하시겠습니까?")) return

    const token = localStorage.getItem("access_token")
    setError("")
    setSuccess("")

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/history/${historyId}/`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })

      if (response.ok) {
        setSuccess("히스토리가 삭제되었습니다.")
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
              <h1 className="text-3xl font-bold text-gray-900">검색 히스토리</h1>
              <p className="text-gray-600 mt-1">부서원들의 검색 기록을 공유합니다</p>
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
                  <p className="text-sm text-gray-600">부서 공유 히스토리</p>
                  <p className="text-2xl font-bold">{sharedHistory.length}개</p>
                </div>
                <Users className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">내 히스토리</p>
                  <p className="text-2xl font-bold">{myHistory.length}개</p>
                </div>
                <User className="h-8 w-8 text-green-600" />
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">총 검색 결과</p>
                  <p className="text-2xl font-bold">
                    {sharedHistory.reduce((sum, h) => sum + h.results_count, 0)}개
                  </p>
                </div>
                <Search className="h-8 w-8 text-purple-600" />
              </div>
            </div>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="shared" className="space-y-4">
            <TabsList>
              <TabsTrigger value="shared">부서 공유</TabsTrigger>
              <TabsTrigger value="my">내 히스토리</TabsTrigger>
            </TabsList>

            {/* 부서 공유 탭 */}
            <TabsContent value="shared">
              <div className="bg-white rounded-lg shadow">
                {sharedHistory.length === 0 ? (
                  <p className="text-center text-gray-500 py-12">공유된 히스토리가 없습니다.</p>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          검색어
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          유형
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          결과 수
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          작성자
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          날짜
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {sharedHistory.map((history) => (
                        <tr key={history.history_id} className="hover:bg-gray-50">
                          <td className="px-4 py-4 text-sm font-medium">{history.query}</td>
                          <td className="px-4 py-4 text-sm">
                            <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                              {history.search_type_display}
                            </span>
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {history.results_count}개
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {history.created_by_name}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {new Date(history.created_at).toLocaleString("ko-KR")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </TabsContent>

            {/* 내 히스토리 탭 */}
            <TabsContent value="my">
              <div className="bg-white rounded-lg shadow">
                {myHistory.length === 0 ? (
                  <p className="text-center text-gray-500 py-12">내 히스토리가 없습니다.</p>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          검색어
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          유형
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          결과 수
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          공유 여부
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
                      {myHistory.map((history) => (
                        <tr key={history.history_id} className="hover:bg-gray-50">
                          <td className="px-4 py-4 text-sm font-medium">{history.query}</td>
                          <td className="px-4 py-4 text-sm">
                            <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                              {history.search_type_display}
                            </span>
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {history.results_count}개
                          </td>
                          <td className="px-4 py-4 text-sm">
                            {history.is_shared ? (
                              <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                                공유됨
                              </span>
                            ) : (
                              <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                                비공개
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {new Date(history.created_at).toLocaleString("ko-KR")}
                          </td>
                          <td className="px-4 py-4 text-sm">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDelete(history.history_id)}
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
