"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { MainLayout } from "@/components/main-layout"
import { Users, Key, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface User {
  user_id: string
  username: string
  email: string
  role: string
  department_name: string
  company_name: string
  status: string
  last_login: string | null
}

interface PasswordResetRequest {
  reset_id: number
  user: string
  user_name: string
  user_email: string
  user_department: string
  requested_by: string
  requested_by_name: string
  status: string
  requested_at: string
  handled_at: string | null
}

export default function DeptAdminPage() {
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [passwordResets, setPasswordResets] = useState<PasswordResetRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [selectedUser, setSelectedUser] = useState<string | null>(null)
  const [tempPassword, setTempPassword] = useState("")
  const [currentUser, setCurrentUser] = useState<any>(null)

  // 알림 메시지 자동 사라지기
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 3000)
      return () => clearTimeout(timer)
    }
  }, [error])

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(""), 3000)
      return () => clearTimeout(timer)
    }
  }, [success])

  // 권한 확인
  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("user") || "{}")
    setCurrentUser(user)
    if (user.role !== "dept_admin") {
      alert("부서 관리자만 접근 가능합니다.")
      router.push("/search")
    }
  }, [router])

  // 데이터 로드
  useEffect(() => {
    if (currentUser) {
      loadUsers()
    }
  }, [currentUser])

  const loadUsers = async () => {
    setLoading(true)
    const token = localStorage.getItem("access_token")

    try {
      // 1. 같은 부서의 모든 사용자 목록 (role 필터 제거)
      const response = await fetch(
        `${API_BASE_URL}/api/accounts/users/?department=${currentUser.department}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      if (response.ok) {
        const data = await response.json()
        setUsers(data.users || data)
      }

      // 2. 비밀번호 초기화 요청 목록
      const resetsRes = await fetch(`${API_BASE_URL}/api/accounts/password-resets/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (resetsRes.ok) {
        const data = await resetsRes.json()
        setPasswordResets(data.resets || [])
      }
    } catch (err) {
      setError("데이터를 불러오는데 실패했습니다.")
    } finally {
      setLoading(false)
    }
  }

  // 비밀번호 초기화
  const handleResetPassword = async () => {
    if (!selectedUser || !tempPassword) {
      setError("사용자와 임시 비밀번호를 입력해주세요.")
      return
    }

    const token = localStorage.getItem("access_token")
    setError("")
    setSuccess("")

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/accounts/users/${selectedUser}/reset-password/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            temp_password: tempPassword,
          }),
        }
      )

      if (response.ok) {
        const data = await response.json()
        setSuccess(`비밀번호가 초기화되었습니다.`)
        setSelectedUser(null)
        setTempPassword("")
        // 데이터 다시 로드
        await loadUsers()
      } else {
        const data = await response.json()
        setError(data.error || "비밀번호 초기화에 실패했습니다.")
      }
    } catch (err) {
      setError("서버 연결에 실패했습니다.")
    }
  }

  // 사용자 상태 변경
  const handleChangeUserStatus = async (userId: string, newStatus: string) => {
    const token = localStorage.getItem("access_token")
    setError("")
    setSuccess("")

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/users/${userId}/status/`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: newStatus }),
      })

      if (response.ok) {
        const data = await response.json()
        setSuccess(data.message || "사용자 상태를 변경했습니다.")
        // 페이지 새로고침 없이 데이터만 다시 로드
        await loadUsers()
      } else {
        const data = await response.json().catch(() => ({ error: "상태 변경에 실패했습니다." }))
        setError(data.error || "상태 변경에 실패했습니다.")
      }
    } catch (err) {
      console.error("Change status error:", err)
      setError("서버 연결에 실패했습니다. 서버가 실행 중인지 확인해주세요.")
    }
  }

  // 사용자 삭제
  const handleDeleteUser = async (userId: string, username: string) => {
    if (!confirm(`정말 사용자 '${username}'을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) {
      return
    }

    const token = localStorage.getItem("access_token")
    setError("")
    setSuccess("")

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/users/${userId}/`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        const data = await response.json()
        setSuccess(data.message || `사용자 '${username}'이(가) 삭제되었습니다.`)
        // 페이지 새로고침 없이 데이터만 다시 로드
        await loadUsers()
      } else {
        const data = await response.json().catch(() => ({ error: "사용자 삭제에 실패했습니다." }))
        setError(data.error || "사용자 삭제에 실패했습니다.")
      }
    } catch (err) {
      console.error("Delete user error:", err)
      setError("서버 연결에 실패했습니다. 서버가 실행 중인지 확인해주세요.")
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
              <h1 className="text-3xl font-bold text-gray-900">부서 관리자 페이지</h1>
              <p className="text-gray-600 mt-1">
                {currentUser?.department_name} 부서를 관리합니다
              </p>
            </div>
            <Button onClick={loadUsers} variant="outline">
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

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">부서 사용자</p>
                    <p className="text-2xl font-bold">{users.length}명</p>
                  </div>
                  <Users className="h-8 w-8 text-blue-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">활성 사용자</p>
                    <p className="text-2xl font-bold">
                      {users.filter((u) => u.status === "active").length}명
                    </p>
                  </div>
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">대기 중인 요청</p>
                    <p className="text-2xl font-bold">
                      {passwordResets.filter(r => r.status === "pending").length}건
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      비밀번호 초기화 요청
                    </p>
                  </div>
                  <Key className="h-8 w-8 text-yellow-600" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="password-resets" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="password-resets">
                비밀번호 초기화
              </TabsTrigger>
              <TabsTrigger value="users">
                사용자 관리
              </TabsTrigger>
            </TabsList>

            {/* 비밀번호 초기화 탭 */}
            <TabsContent value="password-resets" className="space-y-4">
              {/* 비밀번호 초기화 요청 목록 */}
              {passwordResets.filter(r => r.status === "pending").length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>비밀번호 초기화 요청</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          사용자명
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          이메일
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          요청일
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          작업
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {passwordResets
                        .filter(r => r.status === "pending")
                        .map((reset) => (
                          <tr key={reset.reset_id} className="hover:bg-gray-50">
                            <td className="px-4 py-4 text-sm font-medium">{reset.user_name}</td>
                            <td className="px-4 py-4 text-sm text-gray-600">{reset.user_email}</td>
                            <td className="px-4 py-4 text-sm text-gray-600">
                              {new Date(reset.requested_at).toLocaleString("ko-KR")}
                            </td>
                            <td className="px-4 py-4 text-sm">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setSelectedUser(reset.user)}
                                className="bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-300"
                              >
                                비밀번호 초기화
                              </Button>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
              ) : (
                <Card>
                  <CardContent className="p-6 text-center text-gray-500">
                    대기 중인 비밀번호 초기화 요청이 없습니다.
                  </CardContent>
                </Card>
              )}

              {/* 비밀번호 초기화 폼 */}
              {selectedUser && (
                <Card>
                  <CardHeader>
                    <CardTitle>비밀번호 초기화</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>선택된 사용자</Label>
                      <Input
                        value={
                          passwordResets.find((r) => r.user === selectedUser)?.user_name || ""
                        }
                        disabled
                        className="bg-gray-100"
                      />
                    </div>

                    <div>
                      <Label>임시 비밀번호</Label>
                      <div className="flex gap-2 mt-1">
                        <Input
                          type="text"
                          placeholder="최소 8자"
                          value={tempPassword}
                          onChange={(e) => setTempPassword(e.target.value)}
                          minLength={8}
                        />
                        <Button
                          variant="outline"
                          onClick={() => {
                            const randomPassword = Math.random().toString(36).slice(-12)
                            setTempPassword(randomPassword)
                          }}
                        >
                          자동 생성
                        </Button>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button onClick={handleResetPassword} className="flex-1">
                        <Key className="h-4 w-4 mr-2" />
                        비밀번호 초기화
                      </Button>
                      <Button variant="outline" onClick={() => setSelectedUser(null)} className="flex-1">
                        취소
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 완료된 비밀번호 초기화 로그 */}
              {passwordResets.filter(r => r.status === "completed").length > 0 && (
                <Card className="mt-4">
                  <CardHeader>
                    <CardTitle>완료된 비밀번호 초기화 기록</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50 border-b">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">사용자명</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">이메일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">부서</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">요청일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">처리일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">상태</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {passwordResets.filter(r => r.status === "completed").map((reset) => (
                            <tr key={reset.reset_id} className="hover:bg-gray-50">
                              <td className="px-4 py-4 text-sm font-medium">{reset.user_name}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{reset.user_email}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{reset.user_department}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {new Date(reset.requested_at).toLocaleString("ko-KR")}
                              </td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {reset.handled_at ? new Date(reset.handled_at).toLocaleString("ko-KR") : "-"}
                              </td>
                              <td className="px-4 py-4 text-sm">
                                <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                                  완료
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* 사용자 관리 탭 */}
            <TabsContent value="users" className="space-y-4">
              <Card>
            <CardHeader>
              <CardTitle>부서 사용자 목록</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        사용자명
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        이메일
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        역할
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        상태
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        마지막 로그인
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        작업
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {users.map((user) => (
                      <tr key={user.user_id} className="hover:bg-gray-50">
                        <td className="px-4 py-4 text-sm font-medium">{user.username}</td>
                        <td className="px-4 py-4 text-sm text-gray-600">{user.email}</td>
                        <td className="px-4 py-4 text-sm">
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              user.role === "super_admin"
                                ? "bg-purple-100 text-purple-800"
                                : user.role === "dept_admin"
                                ? "bg-blue-100 text-blue-800"
                                : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {user.role === "super_admin"
                              ? "슈퍼관리자"
                              : user.role === "dept_admin"
                              ? "부서관리자"
                              : "일반사용자"}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-sm">
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              user.status === "active"
                                ? "bg-green-100 text-green-800"
                                : user.status === "suspended"
                                ? "bg-red-100 text-red-800"
                                : "bg-yellow-100 text-yellow-800"
                            }`}
                          >
                            {user.status === "active"
                              ? "활성"
                              : user.status === "suspended"
                              ? "정지"
                              : "대기"}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          {user.last_login
                            ? new Date(user.last_login).toLocaleString("ko-KR")
                            : "-"}
                        </td>
                        <td className="px-4 py-4 text-sm">
                          <div className="flex gap-2">
                            {currentUser && user.user_id === currentUser.user_id ? (
                              <span className="text-xs text-gray-400">본인 계정</span>
                            ) : user.role === "super_admin" ? (
                              <span className="text-xs text-gray-400">슈퍼 관리자</span>
                            ) : user.role === "user" ? (
                              <>
                                {user.status === "active" ? (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleChangeUserStatus(user.user_id, "suspended")}
                                    className="bg-yellow-50 hover:bg-yellow-100 text-yellow-700 border-yellow-300"
                                  >
                                    정지
                                  </Button>
                                ) : user.status === "suspended" ? (
                                  <>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleChangeUserStatus(user.user_id, "active")}
                                      className="bg-green-50 hover:bg-green-100 text-green-700 border-green-300"
                                    >
                                      활성화
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="destructive"
                                      onClick={() => handleDeleteUser(user.user_id, user.username)}
                                    >
                                      삭제
                                    </Button>
                                  </>
                                ) : (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleChangeUserStatus(user.user_id, "active")}
                                  >
                                    활성화
                                  </Button>
                                )}
                              </>
                            ) : (
                              <span className="text-xs text-gray-400">-</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </MainLayout>
  )
}
