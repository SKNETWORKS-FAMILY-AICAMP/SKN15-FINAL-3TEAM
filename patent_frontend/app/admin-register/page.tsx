"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { InfoIcon, ShieldCheck } from "lucide-react"

// API 베이스 URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

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

export default function AdminRegisterPage() {
  const router = useRouter()
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

  const handleAdminRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

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
      const response = await fetch(`${API_BASE_URL}/api/accounts/admin/register/`, {
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
        // 토큰 저장 후 대시보드로 이동
        localStorage.setItem("access_token", data.tokens.access)
        localStorage.setItem("refresh_token", data.tokens.refresh)
        localStorage.setItem("user", JSON.stringify(data.user))
        alert(data.message)
        router.push("/search")
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
          setError(data.error || data.detail || "관리자 회원가입에 실패했습니다.")
        }
      }
    } catch (error) {
      console.error("관리자 회원가입 오류:", error)
      setError("서버 연결에 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-transparent p-4">
      <Card className="w-full max-w-2xl shadow-lg bg-white/95 backdrop-blur-sm">
        <CardHeader>
          <div className="flex items-center justify-center mb-2">
            <ShieldCheck className="w-8 h-8 text-blue-600 mr-2" />
            <CardTitle className="text-2xl font-bold text-center">관리자 회원가입</CardTitle>
          </div>
          <CardDescription className="text-center">
            부서 관리자 권한을 요청합니다
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert className="mb-4 bg-blue-50 border-blue-200">
            <InfoIcon className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-sm text-blue-800">
              <strong>관리자 권한 요청</strong>
              <br />회원가입 후 즉시 로그인 가능하며, 관리자 권한은 슈퍼 관리자의 승인 후 부여됩니다.
            </AlertDescription>
          </Alert>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleAdminRegister} className="space-y-4">
            {/* 계정 정보 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="username" className="text-sm font-medium text-gray-700 mb-1 block">
                  아이디 *
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
            </div>

            {/* 이름 정보 */}
            <div className="grid grid-cols-2 gap-4">
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

            {/* 회사 및 부서 */}
            <div className="grid grid-cols-2 gap-4">
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
            </div>

            {/* 비밀번호 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="password" className="text-sm font-medium text-gray-700 mb-1 block">
                  비밀번호 * <span className="text-xs text-gray-500">(최소 8자)</span>
                </Label>
                <Input
                  id="password"
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
            </div>

            <Button
              type="submit"
              className="w-full bg-blue-500 hover:bg-blue-600 text-white"
              disabled={isLoading}
            >
              {isLoading ? "등록 중..." : "관리자로 회원가입"}
            </Button>

            <div className="text-center space-y-2">
              <button
                type="button"
                onClick={() => router.push("/login")}
                className="text-sm text-gray-600 hover:underline"
                disabled={isLoading}
              >
                일반 사용자로 로그인
              </button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
