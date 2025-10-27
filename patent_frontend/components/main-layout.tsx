"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { FileSearch, History, Settings, ShieldCheck, Users, Key, X } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function MainLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<any>(null)
  const [pendingCount, setPendingCount] = useState(0)
  const [showPasswordChange, setShowPasswordChange] = useState(false)
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [passwordError, setPasswordError] = useState("")
  const [passwordSuccess, setPasswordSuccess] = useState("")
  const [isChangingPassword, setIsChangingPassword] = useState(false)

  // 비밀번호 변경 메시지 자동 사라지기
  useEffect(() => {
    if (passwordError) {
      const timer = setTimeout(() => setPasswordError(""), 3000)
      return () => clearTimeout(timer)
    }
  }, [passwordError])

  useEffect(() => {
    if (passwordSuccess) {
      const timer = setTimeout(() => setPasswordSuccess(""), 3000)
      return () => clearTimeout(timer)
    }
  }, [passwordSuccess])

  useEffect(() => {
    const storedUser = localStorage.getItem("user")
    if (storedUser) {
      setUser(JSON.parse(storedUser))
    }
  }, [])

  // 대기 중인 요청 건수 조회
  useEffect(() => {
    if (user && (user.role === "super_admin" || user.role === "dept_admin")) {
      fetchPendingCount()
      // 30초마다 갱신
      const interval = setInterval(fetchPendingCount, 30000)
      return () => clearInterval(interval)
    }
  }, [user])

  const fetchPendingCount = async () => {
    const token = localStorage.getItem("access_token")
    if (!token) return

    try {
      let count = 0

      // 슈퍼 관리자: 관리자 권한 요청 + 비밀번호 초기화 요청
      if (user?.role === "super_admin") {
        const [adminReqRes, passwordReqRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/accounts/admin-requests/`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${API_BASE_URL}/api/accounts/password-resets/`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ])

        if (adminReqRes.ok) {
          const data = await adminReqRes.json()
          const requests = data.requests || data
          count += Array.isArray(requests) ? requests.filter((r: any) => r.status === "pending").length : 0
        }

        if (passwordReqRes.ok) {
          const data = await passwordReqRes.json()
          const resets = data.resets || []
          count += resets.filter((r: any) => r.status === "pending").length
        }
      }
      // 부서 관리자: 비밀번호 초기화 요청만
      else if (user?.role === "dept_admin") {
        const response = await fetch(`${API_BASE_URL}/api/accounts/password-resets/`, {
          headers: { Authorization: `Bearer ${token}` },
        })

        if (response.ok) {
          const data = await response.json()
          const resets = data.resets || []
          count = resets.filter((r: any) => r.status === "pending").length
        }
      }

      setPendingCount(count)
    } catch (err) {
      console.error("Failed to fetch pending count:", err)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem("user")
    router.push("/login")
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError("")
    setPasswordSuccess("")

    // 유효성 검사
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError("모든 필드를 입력해주세요.")
      return
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("새 비밀번호가 일치하지 않습니다.")
      return
    }

    if (newPassword.length < 8) {
      setPasswordError("새 비밀번호는 최소 8자 이상이어야 합니다.")
      return
    }

    setIsChangingPassword(true)
    const token = localStorage.getItem("access_token")

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/change-password/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          old_password: currentPassword,
          new_password: newPassword,
          new_password_confirm: confirmPassword,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setPasswordSuccess("비밀번호가 성공적으로 변경되었습니다.")
        // 폼 초기화
        setCurrentPassword("")
        setNewPassword("")
        setConfirmPassword("")
        // 3초 후 모달 닫기
        setTimeout(() => {
          setShowPasswordChange(false)
        }, 3000)
      } else {
        setPasswordError(data.error || data.old_password?.[0] || data.new_password?.[0] || "비밀번호 변경에 실패했습니다.")
      }
    } catch (err) {
      setPasswordError("서버 연결에 실패했습니다.")
    } finally {
      setIsChangingPassword(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#F9FAFB]">
      <header className="fixed top-0 left-0 right-0 h-16 bg-white shadow-md z-50">
        <div className="h-full px-6 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-foreground hover:text-blue-500 transition-colors">
            특허 분석 시스템
          </Link>

          <nav className="flex items-center gap-8">
            <Link
              href="/search"
              className={`flex items-center gap-2 text-sm font-medium transition-colors relative pb-1 ${
                pathname === "/search" ? "text-blue-500" : "text-foreground hover:text-blue-500"
              }`}
            >
              <FileSearch className="w-4 h-4" />
              통합 검색
              {pathname === "/search" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />}
            </Link>
            <Link
              href="/history"
              className={`flex items-center gap-2 text-sm font-medium transition-colors relative pb-1 ${
                pathname === "/history" ? "text-blue-500" : "text-foreground hover:text-blue-500"
              }`}
            >
              <History className="w-4 h-4" />
              히스토리
              {pathname === "/history" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />}
            </Link>

            {/* 슈퍼 관리자 메뉴 */}
            {user?.role === "super_admin" && (
              <Link
                href="/admin"
                className={`flex items-center gap-2 text-sm font-medium transition-colors relative pb-1 ${
                  pathname === "/admin" ? "text-blue-500" : "text-foreground hover:text-blue-500"
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                슈퍼 관리자
                {pendingCount > 0 && (
                  <span className="absolute -top-1 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {pendingCount}
                  </span>
                )}
                {pathname === "/admin" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />}
              </Link>
            )}

            {/* 부서 관리자 메뉴 */}
            {user?.role === "dept_admin" && (
              <Link
                href="/dept-admin"
                className={`flex items-center gap-2 text-sm font-medium transition-colors relative pb-1 ${
                  pathname === "/dept-admin" ? "text-blue-500" : "text-foreground hover:text-blue-500"
                }`}
              >
                <Users className="w-4 h-4" />
                부서 관리
                {pendingCount > 0 && (
                  <span className="absolute -top-1 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {pendingCount}
                  </span>
                )}
                {pathname === "/dept-admin" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />}
              </Link>
            )}
          </nav>

          <div className="flex items-center gap-4">
            <div className="text-sm text-right">
              <p className="text-gray-900 font-medium">
                {user?.last_name}{user?.first_name}님
              </p>
              <p className="text-xs text-gray-500">
                {user?.role === "super_admin"
                  ? "슈퍼 관리자"
                  : user?.role === "dept_admin"
                  ? "부서 관리자"
                  : "일반 사용자"}
              </p>
            </div>

            {/* 비밀번호 변경 버튼 */}
            <Button
              onClick={() => setShowPasswordChange(true)}
              variant="outline"
              size="sm"
              className="text-sm bg-transparent flex items-center gap-1"
            >
              <Key className="w-3 h-3" />
              비밀번호 변경
            </Button>

            <Button onClick={handleLogout} variant="outline" size="sm" className="text-sm bg-transparent">
              로그아웃
            </Button>
          </div>
        </div>
      </header>

      <main className="pt-16 h-screen">{children}</main>

      {/* 비밀번호 변경 모달 */}
      {showPasswordChange && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-96 max-w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">비밀번호 변경</h2>
              <button
                onClick={() => {
                  setShowPasswordChange(false)
                  setCurrentPassword("")
                  setNewPassword("")
                  setConfirmPassword("")
                  setPasswordError("")
                  setPasswordSuccess("")
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {passwordError && (
              <Alert className="mb-4 bg-red-50 border-red-200">
                <AlertDescription className="text-red-700 text-sm">{passwordError}</AlertDescription>
              </Alert>
            )}

            {passwordSuccess && (
              <Alert className="mb-4 bg-green-50 border-green-200">
                <AlertDescription className="text-green-700 text-sm">{passwordSuccess}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <Label htmlFor="current-password" className="text-sm font-medium text-gray-700 mb-1 block">
                  현재 비밀번호
                </Label>
                <Input
                  id="current-password"
                  type="password"
                  placeholder="현재 비밀번호를 입력하세요"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full"
                  disabled={isChangingPassword}
                />
              </div>

              <div>
                <Label htmlFor="new-password" className="text-sm font-medium text-gray-700 mb-1 block">
                  새 비밀번호 <span className="text-xs text-gray-500">(최소 8자)</span>
                </Label>
                <Input
                  id="new-password"
                  type="password"
                  placeholder="새 비밀번호를 입력하세요"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full"
                  minLength={8}
                  disabled={isChangingPassword}
                />
              </div>

              <div>
                <Label htmlFor="confirm-new-password" className="text-sm font-medium text-gray-700 mb-1 block">
                  새 비밀번호 확인
                </Label>
                <Input
                  id="confirm-new-password"
                  type="password"
                  placeholder="새 비밀번호를 다시 입력하세요"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full"
                  minLength={8}
                  disabled={isChangingPassword}
                />
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowPasswordChange(false)
                    setCurrentPassword("")
                    setNewPassword("")
                    setConfirmPassword("")
                    setPasswordError("")
                    setPasswordSuccess("")
                  }}
                  className="flex-1"
                  disabled={isChangingPassword}
                >
                  취소
                </Button>
                <Button type="submit" className="flex-1 bg-blue-500 hover:bg-blue-600" disabled={isChangingPassword}>
                  {isChangingPassword ? "변경 중..." : "변경하기"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
