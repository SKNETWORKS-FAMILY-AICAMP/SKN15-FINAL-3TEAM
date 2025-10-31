"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { MainLayout } from "@/components/main-layout"
import { Users, Activity, ShieldCheck, Key, CheckCircle, XCircle, UserPlus, Trash2, Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { API_BASE_URL } from "@/lib/config"

interface AdminRequest {
  request_id: number
  request_type: string
  request_type_display: string
  user: string
  user_name: string
  user_email: string
  target_user: string | null
  target_user_name: string | null
  target_user_email: string | null
  company: number | null
  company_name: string | null
  department: number | null
  department_name: string | null
  status: string
  status_display: string
  requested_at: string
  handled_by: string | null
  handled_by_name: string | null
  handled_at: string | null
  comment: string | null
}

interface User {
  user_id: string
  username: string
  email: string
  role: string
  department_name: string
  company_name: string
  status: string
}

interface Department {
  department_id: number
  department_name: string
  company: number
}

export default function AdminPage() {
  const router = useRouter()
  const [userApprovalRequests, setUserApprovalRequests] = useState<AdminRequest[]>([])
  const [approvalLogs, setApprovalLogs] = useState<AdminRequest[]>([])
  const [passwordResetRequests, setPasswordResetRequests] = useState<AdminRequest[]>([])
  const [passwordResetLogs, setPasswordResetLogs] = useState<AdminRequest[]>([])
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [selectedDepartment, setSelectedDepartment] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [selectedRequest, setSelectedRequest] = useState<AdminRequest | null>(null)
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
    if (user.role !== "super_admin" && user.role !== "dept_admin") {
      alert("관리자만 접근 가능합니다.")
      router.push("/search")
    }
  }, [router])

  // 데이터 로드
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    const token = localStorage.getItem("access_token")
    const currentUser = JSON.parse(localStorage.getItem("user") || "{}")

    try {
      // 1. 통합 요청 목록 조회
      const requestsRes = await fetch(`${API_BASE_URL}/api/accounts/admin-requests/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (requestsRes.ok) {
        const data = await requestsRes.json()
        const requests = data.requests || data

        // 회원가입 승인 요청 (pending)
        setUserApprovalRequests(
          Array.isArray(requests)
            ? requests.filter((r: AdminRequest) => r.request_type === "user_approval" && r.status === "pending")
            : []
        )

        // 회원가입 승인 로그 (approved/rejected)
        setApprovalLogs(
          Array.isArray(requests)
            ? requests.filter(
                (r: AdminRequest) =>
                  r.request_type === "user_approval" && (r.status === "approved" || r.status === "rejected")
              )
            : []
        )

        // 비밀번호 초기화 요청 (pending)
        setPasswordResetRequests(
          Array.isArray(requests)
            ? requests.filter((r: AdminRequest) => r.request_type === "password_reset" && r.status === "pending")
            : []
        )

        // 비밀번호 초기화 로그 (approved/rejected)
        setPasswordResetLogs(
          Array.isArray(requests)
            ? requests.filter(
                (r: AdminRequest) =>
                  r.request_type === "password_reset" && (r.status === "approved" || r.status === "rejected")
              )
            : []
        )
      }

      // 2. 부서 목록 조회 (슈퍼관리자만)
      if (currentUser.role === "super_admin") {
        const deptRes = await fetch(
          `${API_BASE_URL}/api/accounts/departments/?company_id=${currentUser.company}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        )
        if (deptRes.ok) {
          const deptData = await deptRes.json()
          setDepartments(deptData || [])
        }
      }

      // 3. 전체 사용자 목록 (같은 회사만)
      const usersRes = await fetch(`${API_BASE_URL}/api/accounts/users/?company=${currentUser.company}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (usersRes.ok) {
        const data = await usersRes.json()
        setAllUsers(data.users || data)
      }
    } catch (err) {
      setError("데이터를 불러오는데 실패했습니다.")
    } finally {
      setLoading(false)
    }
  }

  // 회원가입 승인 요청 처리
  const handleApprovalRequest = async (requestId: number, action: "approved" | "rejected") => {
    const token = localStorage.getItem("access_token")
    setError("")
    setSuccess("")

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/admin-requests/${requestId}/handle/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: action,
          comment: action === "approved" ? "관리자가 승인했습니다." : "관리자가 거부했습니다.",
        }),
      })

      if (response.ok) {
        setSuccess(action === "approved" ? "회원가입을 승인했습니다." : "회원가입을 거부했습니다.")
        loadData()
      } else {
        const data = await response.json()
        setError(data.error || "처리에 실패했습니다.")
      }
    } catch (err) {
      setError("서버 연결에 실패했습니다.")
    }
  }

  // 비밀번호 초기화 처리
  const handlePasswordReset = async (requestId: number) => {
    if (!tempPassword || tempPassword.length < 8) {
      setError("임시 비밀번호는 최소 8자 이상이어야 합니다.")
      return
    }

    const token = localStorage.getItem("access_token")
    setError("")
    setSuccess("")

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/admin-requests/${requestId}/handle/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: "approved",
          temp_password: tempPassword,
          comment: "비밀번호가 초기화되었습니다.",
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setSuccess("비밀번호가 초기화되었습니다.")
        setSelectedRequest(null)
        setTempPassword("")
        loadData()
      } else {
        const data = await response.json()
        setError(data.error || "비밀번호 초기화에 실패했습니다.")
      }
    } catch (err) {
      setError("서버 연결에 실패했습니다.")
    }
  }

  // 비밀번호 요청 거부
  const handleRejectPasswordReset = async (requestId: number) => {
    const token = localStorage.getItem("access_token")
    setError("")
    setSuccess("")

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/admin-requests/${requestId}/handle/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: "rejected",
          comment: "관리자가 거부했습니다.",
        }),
      })

      if (response.ok) {
        setSuccess("비밀번호 초기화 요청을 거부했습니다.")
        loadData()
      } else {
        const data = await response.json()
        setError(data.error || "처리에 실패했습니다.")
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
        await loadData()
      } else {
        const data = await response.json().catch(() => ({ error: "상태 변경에 실패했습니다." }))
        setError(data.error || "상태 변경에 실패했습니다.")
      }
    } catch (err) {
      setError("서버 연결에 실패했습니다.")
    }
  }

  // 관리자 권한 부여 (슈퍼 관리자 전용)
  const handleGrantAdminRole = async (userId: string, username: string) => {
    if (!confirm(`'${username}'님에게 부서 관리자 권한을 부여하시겠습니까?`)) {
      return
    }

    const token = localStorage.getItem("access_token")
    setError("")
    setSuccess("")

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/users/${userId}/role/`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ role: "dept_admin" }),
      })

      if (response.ok) {
        const data = await response.json()
        setSuccess(data.message || "부서 관리자 권한을 부여했습니다.")
        await loadData()
      } else {
        const data = await response.json().catch(() => ({ error: "권한 부여에 실패했습니다." }))
        setError(data.error || "권한 부여에 실패했습니다.")
      }
    } catch (err) {
      setError("서버 연결에 실패했습니다.")
    }
  }

  // 사용자 삭제 (중지된 계정만)
  const handleDeleteUser = async (userId: string, username: string, userStatus: string) => {
    if (userStatus !== "suspended") {
      setError("중지된 계정만 삭제할 수 있습니다.")
      return
    }

    if (!confirm(`'${username}'님의 계정을 영구적으로 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) {
      return
    }

    const token = localStorage.getItem("access_token")
    setError("")
    setSuccess("")

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/users/${userId}/delete/`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.ok) {
        setSuccess(`'${username}'님의 계정이 삭제되었습니다.`)
        await loadData()
      } else {
        const data = await response.json().catch(() => ({ error: "계정 삭제에 실패했습니다." }))
        setError(data.error || "계정 삭제에 실패했습니다.")
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

  const isSuperAdmin = currentUser?.role === "super_admin"
  const isDeptAdmin = currentUser?.role === "dept_admin"

  // 부서별 필터링 함수
  const filterByDepartment = (items: AdminRequest[] | User[]) => {
    if (selectedDepartment === "all") return items

    return items.filter((item) => {
      if ("department_name" in item) {
        // User 타입
        return item.department_name === departments.find((d) => d.department_id.toString() === selectedDepartment)?.department_name
      } else {
        // AdminRequest 타입
        return item.department_name === departments.find((d) => d.department_id.toString() === selectedDepartment)?.department_name
      }
    })
  }

  // 검색 필터링 함수
  const filterBySearch = (items: AdminRequest[] | User[]) => {
    if (!searchQuery.trim()) return items

    const query = searchQuery.toLowerCase()
    return items.filter((item) => {
      if ("user_name" in item) {
        // AdminRequest 타입
        return (
          item.user_name?.toLowerCase().includes(query) ||
          item.user_email?.toLowerCase().includes(query) ||
          item.handled_by_name?.toLowerCase().includes(query)
        )
      } else {
        // User 타입
        return (
          item.username?.toLowerCase().includes(query) ||
          item.email?.toLowerCase().includes(query)
        )
      }
    })
  }

  // 필터링된 데이터 (부서 + 검색)
  const applyFilters = (items: AdminRequest[] | User[]) => {
    let filtered = items
    if (isSuperAdmin) {
      filtered = filterByDepartment(filtered)
    }
    filtered = filterBySearch(filtered)
    return filtered
  }

  const filteredUserApprovalRequests = applyFilters(userApprovalRequests) as AdminRequest[]
  const filteredApprovalLogs = applyFilters(approvalLogs) as AdminRequest[]
  const filteredPasswordResetRequests = applyFilters(passwordResetRequests) as AdminRequest[]
  const filteredPasswordResetLogs = applyFilters(passwordResetLogs) as AdminRequest[]
  const filteredAllUsers = applyFilters(allUsers) as User[]

  return (
    <MainLayout>
      <div className="h-[calc(100vh-4rem)] bg-gray-50 overflow-y-auto">
        <div className="p-6 max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {isSuperAdmin ? "슈퍼 관리자 페이지" : "부서 관리자 페이지"}
              </h1>
              <p className="text-gray-600 mt-1">
                {isSuperAdmin ? "시스템 전체를 관리합니다" : "부서의 사용자를 관리합니다"}
              </p>
            </div>
            <Button onClick={loadData} variant="outline">
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">전체 사용자</p>
                    <p className="text-2xl font-bold">{filteredAllUsers.length}명</p>
                  </div>
                  <Users className="h-8 w-8 text-blue-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">승인 대기</p>
                    <p className="text-2xl font-bold">{userApprovalRequests.length}건</p>
                  </div>
                  <ShieldCheck className="h-8 w-8 text-orange-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">비밀번호 요청</p>
                    <p className="text-2xl font-bold">{filteredPasswordResetRequests.length}건</p>
                  </div>
                  <Key className="h-8 w-8 text-purple-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">활성 사용자</p>
                    <p className="text-2xl font-bold">{filteredAllUsers.filter((u) => u.status === "active").length}명</p>
                  </div>
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 필터링 */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-4 flex-wrap">
                {/* 부서 필터링 (슈퍼관리자만) */}
                {isSuperAdmin && departments.length > 0 && (
                  <>
                    <Label htmlFor="dept-filter" className="text-sm font-medium whitespace-nowrap">
                      부서별 필터:
                    </Label>
                    <Select value={selectedDepartment} onValueChange={setSelectedDepartment}>
                      <SelectTrigger id="dept-filter" className="w-64">
                        <SelectValue>
                          {selectedDepartment === "all"
                            ? "전체 부서"
                            : departments.find((d) => d.department_id.toString() === selectedDepartment)
                                ?.department_name || "부서 선택"}
                        </SelectValue>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">전체 부서</SelectItem>
                        {departments.map((dept) => (
                          <SelectItem key={dept.department_id} value={dept.department_id.toString()}>
                            {dept.department_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <div className="w-px h-8 bg-gray-300" />
                  </>
                )}

                {/* 검색 필터 */}
                <Label htmlFor="search-filter" className="text-sm font-medium whitespace-nowrap">
                  사용자 검색:
                </Label>
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="search-filter"
                    type="text"
                    placeholder="사용자명, 이메일로 검색..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                {searchQuery && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSearchQuery("")}
                    className="text-gray-500"
                  >
                    <XCircle className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Tabs */}
          <Tabs defaultValue="approval" className="space-y-4">
            <TabsList>
              <TabsTrigger value="approval">계정 요청</TabsTrigger>
              <TabsTrigger value="password">비밀번호 변경</TabsTrigger>
              <TabsTrigger value="users">사용자 관리</TabsTrigger>
            </TabsList>

            {/* 계정 요청 탭 */}
            <TabsContent value="approval" className="space-y-4">
              {/* 회원가입 승인 요청 */}
              <Card>
                <CardHeader>
                  <CardTitle>회원가입 승인 요청 목록</CardTitle>
                </CardHeader>
                <CardContent>
                  {filteredUserApprovalRequests.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">대기 중인 회원가입 요청이 없습니다.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50 border-b">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              사용자명
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">이메일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">회사</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">부서</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">요청일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">작업</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {filteredUserApprovalRequests.map((request) => (
                            <tr key={request.request_id} className="hover:bg-gray-50">
                              <td className="px-4 py-4 text-sm font-medium">{request.user_name}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{request.user_email}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{request.company_name || "-"}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{request.department_name || "-"}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {new Date(request.requested_at).toLocaleString("ko-KR")}
                              </td>
                              <td className="px-4 py-4 text-sm space-x-2">
                                <Button
                                  size="sm"
                                  onClick={() => handleApprovalRequest(request.request_id, "approved")}
                                  className="bg-green-600 hover:bg-green-700"
                                >
                                  <CheckCircle className="h-4 w-4 mr-1" />
                                  승인
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => handleApprovalRequest(request.request_id, "rejected")}
                                >
                                  <XCircle className="h-4 w-4 mr-1" />
                                  거부
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* 승인 로그 */}
              {filteredApprovalLogs.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>회원가입 승인 로그</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50 border-b">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              사용자명
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">이메일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">회사</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">부서</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">요청일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">처리일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">처리자</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">결과</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {filteredApprovalLogs.map((log) => (
                            <tr key={log.request_id} className="hover:bg-gray-50">
                              <td className="px-4 py-4 text-sm font-medium">{log.user_name}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{log.user_email}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{log.company_name || "-"}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{log.department_name || "-"}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {new Date(log.requested_at).toLocaleString("ko-KR")}
                              </td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {log.handled_at ? new Date(log.handled_at).toLocaleString("ko-KR") : "-"}
                              </td>
                              <td className="px-4 py-4 text-sm text-gray-600">{log.handled_by_name || "-"}</td>
                              <td className="px-4 py-4 text-sm">
                                <span
                                  className={`px-2 py-1 text-xs rounded-full ${
                                    log.status === "approved"
                                      ? "bg-green-100 text-green-800"
                                      : "bg-red-100 text-red-800"
                                  }`}
                                >
                                  {log.status === "approved" ? "승인" : "거부"}
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

            {/* 비밀번호 변경 탭 */}
            <TabsContent value="password" className="space-y-4">
              {/* 비밀번호 초기화 요청 */}
              <Card>
                <CardHeader>
                  <CardTitle>비밀번호 초기화 요청 목록</CardTitle>
                </CardHeader>
                <CardContent>
                  {filteredPasswordResetRequests.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">대기 중인 비밀번호 초기화 요청이 없습니다.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50 border-b">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">요청자</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              대상자
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              이메일
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">요청일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">작업</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {filteredPasswordResetRequests.map((request) => (
                            <tr key={request.request_id} className="hover:bg-gray-50">
                              <td className="px-4 py-4 text-sm font-medium">{request.user_name}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {request.target_user_name || request.user_name}
                              </td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {request.target_user_email || request.user_email}
                              </td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {new Date(request.requested_at).toLocaleString("ko-KR")}
                              </td>
                              <td className="px-4 py-4 text-sm space-x-2">
                                <Button
                                  size="sm"
                                  onClick={() => setSelectedRequest(request)}
                                  className="bg-blue-600 hover:bg-blue-700"
                                >
                                  <Key className="h-4 w-4 mr-1" />
                                  초기화
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleRejectPasswordReset(request.request_id)}
                                >
                                  거부
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* 비밀번호 초기화 폼 */}
              {selectedRequest && (
                <Card>
                  <CardHeader>
                    <CardTitle>비밀번호 초기화</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>대상 사용자</Label>
                      <Input
                        value={selectedRequest.target_user_name || selectedRequest.user_name}
                        disabled
                        className="bg-gray-100"
                      />
                    </div>

                    <div>
                      <Label>임시 비밀번호 (최소 8자)</Label>
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
                      <Button
                        onClick={() => handlePasswordReset(selectedRequest.request_id)}
                        className="flex-1"
                      >
                        <Key className="h-4 w-4 mr-2" />
                        비밀번호 초기화
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setSelectedRequest(null)
                          setTempPassword("")
                        }}
                        className="flex-1"
                      >
                        취소
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 비밀번호 변경 로그 */}
              {filteredPasswordResetLogs.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>비밀번호 변경 로그</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50 border-b">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">요청자</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              대상자
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              이메일
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">요청일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">처리일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">처리자</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">결과</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {filteredPasswordResetLogs.map((log) => (
                            <tr key={log.request_id} className="hover:bg-gray-50">
                              <td className="px-4 py-4 text-sm font-medium">{log.user_name}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {log.target_user_name || log.user_name}
                              </td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {log.target_user_email || log.user_email}
                              </td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {new Date(log.requested_at).toLocaleString("ko-KR")}
                              </td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {log.handled_at ? new Date(log.handled_at).toLocaleString("ko-KR") : "-"}
                              </td>
                              <td className="px-4 py-4 text-sm text-gray-600">{log.handled_by_name || "-"}</td>
                              <td className="px-4 py-4 text-sm">
                                <span
                                  className={`px-2 py-1 text-xs rounded-full ${
                                    log.status === "approved"
                                      ? "bg-green-100 text-green-800"
                                      : "bg-red-100 text-red-800"
                                  }`}
                                >
                                  {log.status === "approved" ? "완료" : "거부"}
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
            <TabsContent value="users">
              <Card>
                <CardHeader>
                  <CardTitle>전체 사용자 목록</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            사용자명
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">이메일</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            회사/부서
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">역할</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">상태</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">작업</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {filteredAllUsers.map((user) => {
                          const isCurrentUser = currentUser && user.user_id === currentUser.user_id
                          const canManage =
                            !isCurrentUser &&
                            (isSuperAdmin || (isDeptAdmin && user.role === "user"))

                          return (
                            <tr key={user.user_id} className="hover:bg-gray-50">
                              <td className="px-4 py-4 text-sm font-medium">{user.username}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{user.email}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">
                                {user.company_name} / {user.department_name}
                              </td>
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
                              <td className="px-4 py-4 text-sm">
                                <div className="flex gap-2">
                                  {isCurrentUser ? (
                                    <span className="text-xs text-gray-400">본인 계정</span>
                                  ) : !canManage ? (
                                    <span className="text-xs text-gray-400">관리 불가</span>
                                  ) : (
                                    <>
                                      {user.status === "active" && (
                                        <Button
                                          size="sm"
                                          variant="outline"
                                          onClick={() => handleChangeUserStatus(user.user_id, "suspended")}
                                          className="bg-yellow-50 hover:bg-yellow-100 text-yellow-700 border-yellow-300"
                                        >
                                          정지
                                        </Button>
                                      )}
                                      {user.status !== "active" && (
                                        <>
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => handleChangeUserStatus(user.user_id, "active")}
                                            className="bg-green-50 hover:bg-green-100 text-green-700 border-green-300"
                                          >
                                            활성화
                                          </Button>
                                          {user.status === "suspended" && (
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              onClick={() => handleDeleteUser(user.user_id, user.username, user.status)}
                                              className="bg-red-50 hover:bg-red-100 text-red-700 border-red-300"
                                            >
                                              <Trash2 className="h-4 w-4 mr-1" />
                                              삭제
                                            </Button>
                                          )}
                                        </>
                                      )}
                                      {isSuperAdmin && user.role === "user" && user.status === "active" && (
                                        <Button
                                          size="sm"
                                          onClick={() => handleGrantAdminRole(user.user_id, user.username)}
                                          className="bg-blue-600 hover:bg-blue-700"
                                        >
                                          <UserPlus className="h-4 w-4 mr-1" />
                                          관리자 권한 부여
                                        </Button>
                                      )}
                                    </>
                                  )}
                                </div>
                              </td>
                            </tr>
                          )
                        })}
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
