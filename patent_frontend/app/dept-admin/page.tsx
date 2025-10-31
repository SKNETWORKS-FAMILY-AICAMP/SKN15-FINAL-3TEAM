"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

/**
 * 부서 관리자 페이지 - /admin으로 리다이렉트
 *
 * 슈퍼관리자와 부서관리자 페이지가 통합되어
 * 모든 관리 기능은 /admin 페이지에서 권한별로 제공됩니다.
 */
export default function DeptAdminRedirect() {
  const router = useRouter()

  useEffect(() => {
    // /admin 페이지로 리다이렉트
    router.replace("/admin")
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-gray-600">관리자 페이지로 이동 중...</p>
    </div>
  )
}
