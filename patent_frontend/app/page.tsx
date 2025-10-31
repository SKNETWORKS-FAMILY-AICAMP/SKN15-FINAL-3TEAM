"use client"

import { ArrowRight, Search, MessageSquare, TrendingUp, FileEdit, Sparkles, Shield, Zap } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-transparent">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Search className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">PatentAI</span>
            </div>
            <nav className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                기능
              </a>
              <a href="#benefits" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                장점
              </a>
              <a href="#pricing" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                요금제
              </a>
            </nav>
            <Link href="/login">
              <Button variant="default" className="bg-blue-600 hover:bg-blue-700">
                로그인
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-full mb-6">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-600">AI 기반 특허 분석 플랫폼</span>
            </div>
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 text-balance drop-shadow-lg">
              특허 검색과 분석을
              <br />
              <span className="text-blue-300">AI로 혁신하다</span>
            </h1>
            <p className="text-xl text-gray-100 mb-10 text-pretty leading-relaxed max-w-2xl mx-auto drop-shadow-md">
              연구원, 기획자, 관리자를 위한 통합 특허 분석 시스템. AI 챗봇과 고급 검색으로 특허 조사 시간을 90%
              단축하세요.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/login">
                <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-base px-8 h-12">
                  시작하기
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <a href="https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM" target="_blank" rel="noopener noreferrer">
                <Button size="lg" variant="outline" className="text-base px-8 h-12 bg-transparent text-white border-white hover:bg-white/10">
                  자세히 보기
                </Button>
              </a>
            </div>
          </div>

          {/* Hero Image Placeholder */}
          <div className="mt-16 relative">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-gray-200 bg-gradient-to-br from-blue-50 to-gray-50">
              <div className="aspect-[16/9] flex items-center justify-center">
                <img src="/modern-patent-analysis-dashboard-interface-with-sp.jpg" alt="PatentAI Dashboard" className="w-full h-full object-cover" />
              </div>
            </div>
            {/* Floating elements */}
            <div className="absolute -top-4 -left-4 w-24 h-24 bg-blue-600 rounded-2xl opacity-10 blur-2xl" />
            <div className="absolute -bottom-4 -right-4 w-32 h-32 bg-blue-400 rounded-2xl opacity-10 blur-2xl" />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">강력한 기능</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">특허 분석에 필요한 모든 도구를 하나의 플랫폼에서</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Feature 1 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <Search className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">고급 특허 검색</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                제목, 요약, IPC/CPC 코드 등 다양한 조건으로 정확한 특허 검색
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <MessageSquare className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">AI 챗봇 분석</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                유사 특허 찾기, Q&A, 문서 첨삭, 트렌드 분석까지 AI가 도와드립니다
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">트렌드 분석</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                특허 데이터를 시각화하고 기술 트렌드를 한눈에 파악
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <FileEdit className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">문서 첨삭</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                특허 문서를 업로드하고 AI의 개선 제안을 받아보세요
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section id="benefits" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl font-bold text-gray-900 mb-6">
                왜 PatentAI를
                <br />
                선택해야 할까요?
              </h2>
              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Zap className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">90% 시간 절약</h3>
                    <p className="text-gray-600 text-sm leading-relaxed">
                      AI 기반 검색과 분석으로 특허 조사 시간을 대폭 단축
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Shield className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">정확한 분석</h3>
                    <p className="text-gray-600 text-sm leading-relaxed">
                      최신 AI 모델로 유사 특허를 정확하게 찾고 분석
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">통합 워크플로우</h3>
                    <p className="text-gray-600 text-sm leading-relaxed">
                      검색부터 분석, 문서 작성까지 하나의 플랫폼에서
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="relative rounded-2xl overflow-hidden shadow-xl border border-gray-200">
                <img src="/ai-chatbot-analyzing-patent-documents-with-charts-.jpg" alt="AI Analysis" className="w-full h-full object-cover" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-12 bg-gray-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">요금제</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">합리적인 가격으로 강력한 AI 특허 분석을 경험하세요</p>
          </div>

          <div className="max-w-3xl mx-auto">
            <div className="bg-white rounded-xl shadow-lg border-2 border-blue-600 p-6 md:p-8">
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="flex-1">
                  <div className="inline-block px-3 py-1 bg-blue-100 text-blue-600 rounded-full text-xs font-medium mb-3">
                    추천
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-3">Pro Plan</h3>
                  <ul className="space-y-2">
                    <li className="flex items-start gap-2">
                      <div className="flex-shrink-0 w-4 h-4 bg-blue-100 rounded-full flex items-center justify-center mt-0.5">
                        <svg className="w-2.5 h-2.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <span className="text-sm text-gray-700">무제한 특허 검색</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <div className="flex-shrink-0 w-4 h-4 bg-blue-100 rounded-full flex items-center justify-center mt-0.5">
                        <svg className="w-2.5 h-2.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <span className="text-sm text-gray-700">AI 챗봇 분석</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <div className="flex-shrink-0 w-4 h-4 bg-blue-100 rounded-full flex items-center justify-center mt-0.5">
                        <svg className="w-2.5 h-2.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <span className="text-sm text-gray-700">문서 첨삭 기능</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <div className="flex-shrink-0 w-4 h-4 bg-blue-100 rounded-full flex items-center justify-center mt-0.5">
                        <svg className="w-2.5 h-2.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <span className="text-sm text-gray-700">부서 공유 기능</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <div className="flex-shrink-0 w-4 h-4 bg-blue-100 rounded-full flex items-center justify-center mt-0.5">
                        <svg className="w-2.5 h-2.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <span className="text-sm text-gray-700">24/7 고객 지원</span>
                    </li>
                  </ul>
                </div>
                <div className="flex-shrink-0 text-center">
                  <div className="mb-4">
                    <div className="flex items-baseline justify-center gap-1">
                      <span className="text-4xl font-bold text-gray-900">₩30,000</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">월 사용료</p>
                  </div>
                  <Link href="/login">
                    <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-base px-8 h-11 w-full">
                      결제하기
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section id="cta" className="py-20 bg-gradient-to-br from-blue-600 to-blue-700">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-6">지금 바로 시작하세요</h2>
          <p className="text-xl text-blue-100 mb-10 max-w-2xl mx-auto">
            무료 체험으로 PatentAI의 강력한 기능을 경험해보세요. 신용카드 등록 없이 바로 시작할 수 있습니다.
          </p>
          <Link href="/login">
            <Button
              size="lg"
              variant="secondary"
              className="bg-white text-blue-600 hover:bg-gray-100 text-base px-8 h-12"
            >
              무료로 시작하기
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Search className="w-5 h-5 text-white" />
                </div>
                <span className="text-lg font-bold text-white">PatentAI</span>
              </div>
              <p className="text-sm leading-relaxed">AI 기반 특허 분석 플랫폼</p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">제품</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    기능
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    요금제
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    API
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">회사</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    소개
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    블로그
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    채용
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">지원</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    문서
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    고객지원
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    문의하기
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-sm text-center">
            <p>&copy; 2025 PatentAI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
