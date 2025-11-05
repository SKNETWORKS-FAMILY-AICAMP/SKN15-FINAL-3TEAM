import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "VeraClaim | AI 특허 분석 플랫폼",
  description: "AI 기반 특허 검색, 분석 및 거절 사유 확인 서비스. 특허 정보를 빠르고 정확하게 찾아보세요.",
  keywords: ["특허", "특허검색", "AI", "특허분석", "거절사유", "심사의견", "논문검색"],
  authors: [{ name: "VeraClaim Team" }],
  openGraph: {
    title: "VeraClaim - AI 특허 분석 플랫폼",
    description: "AI 기반 특허 검색 및 분석 서비스",
    type: "website",
    locale: "ko_KR",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ko">
      <body className={`${inter.className} font-sans antialiased`}>
        {/* Background Image - 모든 페이지에 적용 */}
        <div className="fixed inset-0 z-0">
          {/* 배경 이미지 */}
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: "url(/pexels-august-de-richelieu-4427422.jpg)",
              backgroundSize: "cover",
              backgroundPosition: "center",
              backgroundRepeat: "no-repeat",
            }}
          />

          {/* 어두운 오버레이 - 텍스트 가독성 향상 */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-900/80 via-gray-900/70 to-blue-800/80" />
        </div>

        {/* Content - 배경 위에 표시 */}
        <div className="relative z-10">
          {children}
        </div>

        <Analytics />
      </body>
    </html>
  )
}
