"use client"
import { API_BASE_URL } from "@/lib/config"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"

// API 베이스 URL

interface Company {
  company_id: number
  name: string
  domain: string
}

interface Department {
  department_id: number
  company: number
  company_name: string
  name: string
}

export default function LoginPage() {
  const router = useRouter()
  const [isSignup, setIsSignup] = useState(false)
  const [isPasswordRequest, setIsPasswordRequest] = useState(false)
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [email, setEmail] = useState("")
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [selectedCompany, setSelectedCompany] = useState<number | null>(null)
  const [selectedDepartment, setSelectedDepartment] = useState<number | null>(null)
  const [companies, setCompanies] = useState<Company[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [filteredDepartments, setFilteredDepartments] = useState<Department[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

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

  // 회사 목록 불러오기
  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/accounts/companies/`)
        if (response.ok) {
          const data = await response.json()
          setCompanies(data)
        }
      } catch (error) {
        console.error("회사 목록 불러오기 실패:", error)
      }
    }

    const fetchDepartments = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/accounts/departments/`)
        if (response.ok) {
          const data = await response.json()
          setDepartments(data)
        }
      } catch (error) {
        console.error("부서 목록 불러오기 실패:", error)
      }
    }

    fetchCompanies()
    fetchDepartments()
  }, [])

  // 회사 선택 시 해당 회사의 부서만 필터링
  useEffect(() => {
    if (selectedCompany) {
      const filtered = departments.filter((dept) => dept.company === selectedCompany)
      setFilteredDepartments(filtered)
    } else {
      setFilteredDepartments([])
    }
  }, [selectedCompany, departments])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          password,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        // JWT 토큰 저장
        localStorage.setItem("access_token", data.tokens.access)
        localStorage.setItem("refresh_token", data.tokens.refresh)
        localStorage.setItem("user", JSON.stringify(data.user))

        // 모든 사용자를 통합검색 페이지로 이동
        router.push("/search")
      } else {
        setError(data.error || "로그인에 실패했습니다.")
      }
    } catch (error) {
      console.error("로그인 오류:", error)
      setError("서버 연결에 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    // 아이디 유효성 검사 (영어, 숫자, 언더스코어만 허용)
    const usernameRegex = /^[a-zA-Z0-9_]+$/
    if (!usernameRegex.test(username)) {
      setError("아이디는 영어, 숫자, 언더스코어(_)만 사용할 수 있습니다")
      setIsLoading(false)
      return
    }

    // 비밀번호 확인
    if (password !== confirmPassword) {
      setError("비밀번호가 일치하지 않습니다")
      setIsLoading(false)
      return
    }

    // 회사 및 부서 선택 확인
    if (!selectedCompany || !selectedDepartment) {
      setError("회사와 부서를 선택해주세요")
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/register/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          email,
          password,
          password_confirm: confirmPassword,
          first_name: firstName,
          last_name: lastName,
          company: selectedCompany,
          department: selectedDepartment,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        alert("회원가입이 완료되었습니다. 관리자 승인 후 로그인 가능합니다.")
        setIsSignup(false)
        // 폼 초기화
        setUsername("")
        setEmail("")
        setPassword("")
        setConfirmPassword("")
        setFirstName("")
        setLastName("")
        setSelectedCompany(null)
        setSelectedDepartment(null)
      } else {
        // 백엔드 에러 메시지 처리
        if (data.username) {
          setError(data.username[0])
        } else if (data.email) {
          setError(data.email[0])
        } else if (data.password) {
          setError(data.password[0])
        } else if (data.password_confirm) {
          setError(data.password_confirm[0])
        } else if (data.non_field_errors) {
          setError(data.non_field_errors[0])
        } else {
          setError(data.error || "회원가입에 실패했습니다.")
        }
      }
    } catch (error) {
      console.error("회원가입 오류:", error)
      setError("서버 연결에 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  const handlePasswordRequest = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")
    setSuccess("")

    // 필수 입력값 확인
    if (!username || !email || !selectedCompany || !selectedDepartment) {
      setError("모든 정보를 입력해주세요")
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/password-resets/request-anonymous/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          email,
          company: selectedCompany,
          department: selectedDepartment,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess("비밀번호 초기화 요청이 관리자에게 전달되었습니다.")
        // 폼 초기화
        setUsername("")
        setEmail("")
        setSelectedCompany(null)
        setSelectedDepartment(null)
        // 3초 후 로그인 화면으로 전환
        setTimeout(() => {
          setIsPasswordRequest(false)
        }, 3000)
      } else {
        setError(data.error || "비밀번호 요청에 실패했습니다.")
      }
    } catch (error) {
      console.error("비밀번호 요청 오류:", error)
      setError("서버 연결에 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-transparent">
      <Card className="w-96 shadow-lg bg-white/95 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">
            {isPasswordRequest ? "비밀번호 요청" : isSignup ? "회원가입" : "특허 분석 시스템"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-md text-sm">
              {success}
            </div>
          )}

          {isPasswordRequest ? (
            <form onSubmit={handlePasswordRequest} className="space-y-4">
              <div>
                <Label htmlFor="request-username" className="text-sm font-medium text-gray-700 mb-1 block">
                  아이디 *
                </Label>
                <Input
                  id="request-username"
                  type="text"
                  placeholder="아이디를 입력하세요"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full"
                  required
                  disabled={isLoading}
                />
              </div>
              <div>
                <Label htmlFor="request-email" className="text-sm font-medium text-gray-700 mb-1 block">
                  이메일 *
                </Label>
                <Input
                  id="request-email"
                  type="email"
                  placeholder="example@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full"
                  required
                  disabled={isLoading}
                />
              </div>
              <div>
                <Label htmlFor="request-company" className="text-sm font-medium text-gray-700 mb-1 block">
                  회사 *
                </Label>
                <Select
                  value={selectedCompany?.toString() || ""}
                  onValueChange={(value) => {
                    setSelectedCompany(Number(value))
                    setSelectedDepartment(null)
                  }}
                  disabled={isLoading}
                  required
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="회사를 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    {companies.map((company) => (
                      <SelectItem key={company.company_id} value={company.company_id.toString()}>
                        {company.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="request-department" className="text-sm font-medium text-gray-700 mb-1 block">
                  부서 *
                </Label>
                <Select
                  value={selectedDepartment?.toString() || ""}
                  onValueChange={(value) => setSelectedDepartment(Number(value))}
                  disabled={isLoading || !selectedCompany}
                  required
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={selectedCompany ? "부서를 선택하세요" : "먼저 회사를 선택하세요"} />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredDepartments.map((dept) => (
                      <SelectItem key={dept.department_id} value={dept.department_id.toString()}>
                        {dept.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                type="submit"
                className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                disabled={isLoading}
              >
                {isLoading ? "요청 중..." : "비밀번호 초기화 요청"}
              </Button>
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setIsPasswordRequest(false)
                    setError("")
                    setSuccess("")
                  }}
                  className="text-sm text-gray-600 hover:underline"
                  disabled={isLoading}
                >
                  로그인으로 돌아가기
                </button>
              </div>
            </form>
          ) : !isSignup ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="username" className="text-sm font-medium text-gray-700 mb-1 block">
                  아이디
                </Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="아이디를 입력하세요"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full"
                  required
                  disabled={isLoading}
                />
              </div>
              <div>
                <Label htmlFor="password" className="text-sm font-medium text-gray-700 mb-1 block">
                  비밀번호
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="비밀번호를 입력하세요"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full"
                  required
                  disabled={isLoading}
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                disabled={isLoading}
              >
                {isLoading ? "로그인 중..." : "로그인"}
              </Button>
              <div className="text-center space-y-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsSignup(true)
                    setError("")
                  }}
                  className="text-sm text-blue-500 hover:underline block w-full"
                >
                  회원가입
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsPasswordRequest(true)
                    setError("")
                  }}
                  className="text-sm text-orange-500 hover:underline block w-full"
                >
                  비밀번호 초기화 요청
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleSignup} className="space-y-4">
              <div>
                <Label htmlFor="signup-username" className="text-sm font-medium text-gray-700 mb-1 block">
                  아이디 *
                </Label>
                <Input
                  id="signup-username"
                  type="text"
                  placeholder="아이디를 입력하세요"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full"
                  required
                  disabled={isLoading}
                />
              </div>
              <div>
                <Label htmlFor="email" className="text-sm font-medium text-gray-700 mb-1 block">
                  이메일 *
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="example@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full"
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="last-name" className="text-sm font-medium text-gray-700 mb-1 block">
                    성
                  </Label>
                  <Input
                    id="last-name"
                    type="text"
                    placeholder="홍"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full"
                    disabled={isLoading}
                  />
                </div>
                <div>
                  <Label htmlFor="first-name" className="text-sm font-medium text-gray-700 mb-1 block">
                    이름
                  </Label>
                  <Input
                    id="first-name"
                    type="text"
                    placeholder="길동"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full"
                    disabled={isLoading}
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="company" className="text-sm font-medium text-gray-700 mb-1 block">
                  회사 *
                </Label>
                <Select
                  value={selectedCompany?.toString() || ""}
                  onValueChange={(value) => {
                    setSelectedCompany(Number(value))
                    setSelectedDepartment(null)
                  }}
                  disabled={isLoading}
                  required
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="회사를 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    {companies.map((company) => (
                      <SelectItem key={company.company_id} value={company.company_id.toString()}>
                        {company.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="department" className="text-sm font-medium text-gray-700 mb-1 block">
                  부서 *
                </Label>
                <Select
                  value={selectedDepartment?.toString() || ""}
                  onValueChange={(value) => setSelectedDepartment(Number(value))}
                  disabled={isLoading || !selectedCompany}
                  required
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={selectedCompany ? "부서를 선택하세요" : "먼저 회사를 선택하세요"} />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredDepartments.map((dept) => (
                      <SelectItem key={dept.department_id} value={dept.department_id.toString()}>
                        {dept.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="signup-password" className="text-sm font-medium text-gray-700 mb-1 block">
                  비밀번호 * <span className="text-xs text-gray-500">(최소 8자)</span>
                </Label>
                <Input
                  id="signup-password"
                  type="password"
                  placeholder="비밀번호를 입력하세요"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full"
                  required
                  minLength={8}
                  disabled={isLoading}
                />
              </div>
              <div>
                <Label htmlFor="confirm-password" className="text-sm font-medium text-gray-700 mb-1 block">
                  비밀번호 확인 *
                </Label>
                <Input
                  id="confirm-password"
                  type="password"
                  placeholder="비밀번호를 다시 입력하세요"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full"
                  required
                  minLength={8}
                  disabled={isLoading}
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                disabled={isLoading}
              >
                {isLoading ? "회원가입 중..." : "회원가입"}
              </Button>
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setIsSignup(false)
                    setError("")
                  }}
                  className="text-sm text-gray-600 hover:underline"
                  disabled={isLoading}
                >
                  로그인으로 돌아가기
                </button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
