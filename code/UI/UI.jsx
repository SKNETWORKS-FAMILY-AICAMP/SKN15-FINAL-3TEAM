import React, { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Upload, Search, Bot, Send, Filter, Settings, BarChart3, History, Sparkles, ShieldCheck, Users, Plus, Trash2, ChevronRight, LogIn } from "lucide-react";
import { ResponsiveContainer, CartesianGrid, XAxis, YAxis, Tooltip, Legend, AreaChart, Area } from "recharts";

// ---------------------------------------------
// Dummy data for the mockup (replace with real API wiring later)
// ---------------------------------------------
const dummyUsers = [
  { id: "sojung", team: "R&D", role: "user", lastActive: "2025-10-01" },
  { id: "solchan", team: "IP-Analyst", role: "admin", lastActive: "2025-10-04" },
  { id: "noh", team: "Legal", role: "user", lastActive: "2025-10-06" },
];

const dummyTrends = [
  { month: "2025-01", filings: 3200, rejections: 840, designs: 1200 },
  { month: "2025-02", filings: 3350, rejections: 790, designs: 1140 },
  { month: "2025-03", filings: 3100, rejections: 870, designs: 1180 },
  { month: "2025-04", filings: 3600, rejections: 910, designs: 1220 },
  { month: "2025-05", filings: 3720, rejections: 880, designs: 1190 },
  { month: "2025-06", filings: 3550, rejections: 920, designs: 1210 },
  { month: "2025-07", filings: 3810, rejections: 899, designs: 1250 },
  { month: "2025-08", filings: 3900, rejections: 940, designs: 1270 },
  { month: "2025-09", filings: 4020, rejections: 965, designs: 1295 },
];

const cannedPrompts = [
  { title: "거절사유 요약", prompt: "첨부된 명세서에서 주요 거절사유를 요약해줘" },
  { title: "신규성 검토", prompt: "아래 키워드 기반으로 신규성/진보성 위험 요소를 찾아줘" },
  { title: "유사 특허 Top-K", prompt: "아이디어 설명을 요약하고 Top-K 유사 특허를 보여줘" },
];

const exampleHits = [
  { id: "KR10-2024-123456", title: "드론 영상 기반 균열 탐지 방법", score: 92, where: ["제목", "요약"], snippet: "… 딥러닝 모델로 콘크리트 균열을 자동 탐지 …" },
  { id: "US11-2023-888888", title: "건축 표면 결함 검출 시스템", score: 87, where: ["본문"], snippet: "… CNN과 열화상 데이터 융합 …" },
  { id: "JP-2022-777777", title: "균열 깊이 추정 장치", score: 80, where: ["본문"], snippet: "… 다중 스케일 특징 기반 회귀 …" },
  { id: "EP-2021-555555", title: "UAV 점검 자동화", score: 74, where: ["요약"], snippet: "… 경로 최적화 및 결함 후보군 랭킹 …" },
];

// ---------------------------------------------
// Pure helpers for layout math (facilitates tests and avoids UI coupling)
// ---------------------------------------------
export function computeNextLeftWidth(startLeftPct, deltaPx, containerWidthPx) {
  const min = 20;
  const max = 70;
  if (!containerWidthPx || !Number.isFinite(containerWidthPx)) return startLeftPct;
  const changePct = (deltaPx / containerWidthPx) * 100;
  const next = startLeftPct + changePct;
  return Math.min(max, Math.max(min, next));
}

export function safeGetSplitContainer(handleEl) {
  // handle → parent (divider wrapper) → parent (row container)
  if (!handleEl) return null;
  const p1 = handleEl.parentElement; // may be null in some render timing
  if (!p1) return null;
  const p2 = p1.parentElement;
  return p2 ?? null;
}

// ---------------------------------------------
// Profile helpers
// ---------------------------------------------
export function validatePasswordChange(currentPw, newPw, confirmPw) {
  if (!currentPw || !newPw || !confirmPw) return { ok: false, reason: "모든 비밀번호 필드를 입력하세요" };
  if (newPw.length < 8) return { ok: false, reason: "새 비밀번호는 8자 이상이어야 합니다" };
  if (newPw === currentPw) return { ok: false, reason: "새 비밀번호가 현재와 동일합니다" };
  if (newPw !== confirmPw) return { ok: false, reason: "새 비밀번호와 확인이 일치하지 않습니다" };
  return { ok: true, reason: "" };
}

// Admin-only: set a new password without current password
export function validatePasswordSetAdmin(newPw, confirmPw) {
  if (!newPw || !confirmPw) return { ok: false, reason: "새 비밀번호와 확인을 입력하세요" };
  if (newPw.length < 8) return { ok: false, reason: "새 비밀번호는 8자 이상이어야 합니다" };
  if (newPw !== confirmPw) return { ok: false, reason: "새 비밀번호와 확인이 일치하지 않습니다" };
  return { ok: true, reason: "" };
}

// Admin helper: build a normalized user record (pure for tests)
export function buildUserRecord(id, team, role) {
  return { id, team, role, lastActive: "-" };
}

// ---------------------------------------------
// UI Bits
// ---------------------------------------------
function Toolbar() {
  return (
    <div className="w-full flex items-center justify-between p-3 md:p-4 border-b bg-background/60 backdrop-blur supports-[backdrop-filter]:bg-background/40 sticky top-0 z-50">
      <div className="flex items-center gap-2">
        <Bot className="h-6 w-6" />
        <span className="font-semibold text-lg">Veraclaim</span>
        <Badge variant="secondary" className="ml-2 rounded-full">AI Hub</Badge>
      </div>
      <div className="hidden md:flex items-center gap-2">
        <Button variant="ghost" size="sm"><BarChart3 className="h-4 w-4 mr-2"/>Trends</Button>
        <Button variant="ghost" size="sm"><History className="h-4 w-4 mr-2"/>History</Button>
        <Separator orientation="vertical" className="mx-2 h-6"/>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm"><Settings className="h-4 w-4 mr-2"/>Settings</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>Workspace</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuCheckboxItem checked>자동 저장</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem>실험적 기능</DropdownMenuCheckboxItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>테마 전환</DropdownMenuItem>
            <DropdownMenuItem>단축키</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

function CannedPromptBar({ onUse }) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2">
      {cannedPrompts.map((c, i) => (
        <Button key={i} variant="outline" size="sm" onClick={()=>onUse(c.prompt)}>
          <Sparkles className="h-4 w-4 mr-2"/>{c.title}
        </Button>
      ))}
    </div>
  );
}

function HitItem({ hit }) {
  return (
    <div className="flex items-start justify-between p-3 rounded-xl border hover:shadow-sm">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{hit.id}</Badge>
          <span className="font-medium">{hit.title}</span>
        </div>
        <div className="text-muted-foreground text-sm">스코어 {hit.score}% · 위치: {hit.where.join(", ")}</div>
        <div className="text-sm">{hit.snippet}</div>
      </div>
      <Button variant="ghost" size="icon"><ChevronRight className="h-4 w-4"/></Button>
    </div>
  );
}

function TrendPanel() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5"/>트렌드</CardTitle>
        <CardDescription>월별 출원/거절/디자인 동향</CardDescription>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={dummyTrends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month"/>
            <YAxis />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="filings" name="출원" stroke="currentColor" fillOpacity={0.2} fill="currentColor" />
            <Area type="monotone" dataKey="rejections" name="거절" stroke="currentColor" fillOpacity={0.2} fill="currentColor" />
            <Area type="monotone" dataKey="designs" name="디자인" stroke="currentColor" fillOpacity={0.2} fill="currentColor" />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function RightChatPane({ historyOpen, setHistoryOpen }) {
  const [msg, setMsg] = useState("");
  const [messages, setMessages] = useState([
    { role: "system", text: "특허 도메인 보조 챗봇입니다. 무엇을 도와드릴까요?" },
    { role: "user", text: "드론 균열탐지 신규성 확인해줘" },
    { role: "assistant", text: "관련 선행기술 4건을 정리했어요." },
  ]);
  const send = () => {
    if (!msg.trim()) return;
    setMessages(prev => [...prev, { role: "user", text: msg }]);
    setMsg("");
    setTimeout(()=> setMessages(prev => [...prev, { role: "assistant", text: "모형 응답: 거절사유 후보(신규성, 명확성)" }]), 300);
  };
  return (
    <div className="h-full flex flex-col rounded-2xl border overflow-hidden">
      <div className="p-3 border-b flex items-center justify-between bg-muted/40">
        <div className="flex items-center gap-2"><Bot className="h-4 w-4"/><span className="font-medium">AI Assist</span></div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={()=>setHistoryOpen(true)}><History className="h-4 w-4 mr-2"/>History</Button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${m.role === "user" ? "ml-auto bg-primary text-primary-foreground" : m.role === "assistant" ? "bg-card" : "bg-muted/60"}`}>
            {m.text}
          </div>
        ))}
      </div>
      <div className="border-t p-2 flex items-center gap-2">
        <Input placeholder="메시지를 입력하세요…" value={msg} onChange={e=>setMsg(e.target.value)} onKeyDown={e=>{ if(e.key==='Enter') send();}}/>
        <Button onClick={send}><Send className="h-4 w-4 mr-2"/>보내기</Button>
      </div>
    </div>
  );
}

function KeywordSearchPane() {
  const [keyword, setKeyword] = useState("");
  const matches = useMemo(() => exampleHits.filter(h => keyword ? h.title.includes(keyword) || h.snippet.includes(keyword) : true), [keyword]);
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2"><Search className="h-5 w-5"/>키워드 검색</CardTitle>
          <CardDescription>제목/내용 키워드 매칭</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Input placeholder="예: 균열 탐지, crack" value={keyword} onChange={e=>setKeyword(e.target.value)}/>
            <Button variant="secondary"><Filter className="h-4 w-4 mr-2"/>필터</Button>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline"><Upload className="h-4 w-4 mr-2"/>첨부파일</Button>
            <Badge variant="secondary" className="rounded-full">PDF 0</Badge>
            <Badge variant="secondary" className="rounded-full">Images 0</Badge>
          </div>
          <div className="space-y-2">
            {matches.slice(0,4).map(m => <HitItem key={m.id} hit={m}/>) }
          </div>
        </CardContent>
      </Card>
      <TrendPanel />
    </div>
  );
}

function AdminView() {
  const [users, setUsers] = useState(dummyUsers);
  const [create, setCreate] = useState({ id: "", pw: "", team: "R&D", role: "user", notify: true });
  const [msg, setMsg] = useState("");

  // list filters
  const [q, setQ] = useState("");
  const [teamFilter, setTeamFilter] = useState("ALL");

  const deleteUser = (id) => setUsers(prev => prev.filter(u => u.id !== id));
  const submitCreate = () => {
    if (!create.id || !create.pw) { setMsg("아이디와 임시 비밀번호를 입력하세요"); return; }
    const rec = buildUserRecord(create.id, create.team, create.role);
    setUsers(prev => [rec, ...prev]);
    setMsg(`계정이 생성되었습니다: ${create.id} (${create.team}/${create.role})`);
    setCreate(s=>({ ...s, id: "", pw: "" }));
  };

  // filtering logic (case-insensitive)
  const filtered = users.filter(u => {
    const okTeam = teamFilter === 'ALL' ? true : (u.team === teamFilter);
    if (!q.trim()) return okTeam;
    const t = q.trim().toLowerCase();
    return okTeam && (u.id.toLowerCase().includes(t) || (u.team||'').toLowerCase().includes(t));
  });

  return (
    <div className="p-4 md:p-6 space-y-6">
      {msg && (
        <Alert>
          <AlertTitle>알림</AlertTitle>
          <AlertDescription>{msg}</AlertDescription>
        </Alert>
      )}
      <Alert>
        <ShieldCheck className="h-4 w-4" />
        <AlertTitle>Admin 콘솔</AlertTitle>
        <AlertDescription>계정 생성/삭제, 팀 권한 관리</AlertDescription>
      </Alert>
      <Card>
        <CardHeader>
          <CardTitle>계정 생성</CardTitle>
          <CardDescription>신규 사용자 계정과 임시 비밀번호 발급</CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-4 gap-3">
          <div className="col-span-2 space-y-2">
            <Label>아이디</Label>
            <Input placeholder="e.g. jhkim" value={create.id} onChange={e=>setCreate(s=>({...s,id:e.target.value}))}/>
          </div>
          <div className="col-span-2 space-y-2">
            <Label>임시 비밀번호</Label>
            <Input placeholder="Auto-generated" value={create.pw} onChange={e=>setCreate(s=>({...s,pw:e.target.value}))}/>
          </div>
          <div className="col-span-2 space-y-2">
            <Label>팀</Label>
            <select className="border rounded-md px-3 py-2 w-full" value={create.team} onChange={e=>setCreate(s=>({...s,team:e.target.value}))}>
              <option>R&D</option>
              <option>IP-Analyst</option>
              <option>Legal</option>
            </select>
          </div>
          <div className="col-span-2 space-y-2">
            <Label>권한</Label>
            <select className="border rounded-md px-3 py-2 w-full" value={create.role} onChange={e=>setCreate(s=>({...s,role:e.target.value}))}>
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <div className="col-span-4 flex items-center gap-2">
            <Switch checked={create.notify} onCheckedChange={(v)=>setCreate(s=>({...s,notify:v}))}/>
            <span className="text-sm text-muted-foreground">요청 시 관리자 알림</span>
          </div>
          <div className="col-span-4">
            <Button onClick={submitCreate}><Plus className="h-4 w-4 mr-2"/>계정 생성</Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>사용자 목록</CardTitle>
          <CardDescription>아이디/팀으로 빠르게 검색하세요</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-col md:flex-row md:items-center gap-2">
            <Input placeholder="아이디 또는 팀으로 검색" value={q} onChange={(e)=>setQ(e.target.value)} className="md:w-72"/>
            <select className="border rounded-md px-3 py-2 md:w-48" value={teamFilter} onChange={(e)=>setTeamFilter(e.target.value)}>
              <option value="ALL">모든 팀</option>
              <option value="R&D">R&D</option>
              <option value="IP-Analyst">IP-Analyst</option>
              <option value="Legal">Legal</option>
            </select>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>아이디</TableHead>
                <TableHead>팀</TableHead>
                <TableHead>권한</TableHead>
                <TableHead>최근 접속</TableHead>
                <TableHead className="text-right">작업</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map(u=> (
                <TableRow key={u.id}>
                  <TableCell>{u.id}</TableCell>
                  <TableCell>{u.team}</TableCell>
                  <TableCell><Badge variant={u.role==="admin"?"default":"secondary"}>{u.role}</Badge></TableCell>
                  <TableCell>{u.lastActive}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={()=>deleteUser(u.id)}>
                      <Trash2 className="h-4 w-4"/>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-sm text-muted-foreground">검색 결과가 없습니다</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function UserProfileView() {
  const [form, setForm] = useState({ id: "sojung", team: "R&D", role: "user" });
  const [pw, setPw] = useState({ next: "", confirm: "" }); // Admin reset: no current
  const [msg, setMsg] = useState("");
  const saveProfile = () => {
    setMsg("프로필이 저장되었습니다 (mock)");
  };
  const changePw = () => {
    const res = validatePasswordSetAdmin(pw.next, pw.confirm);
    if (!res.ok) { setMsg(res.reason); return; }
    setMsg("비밀번호가 변경되었습니다 (관리자 재설정, mock)");
    setPw({ next: "", confirm: "" });
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      {msg && (
        <Alert>
          <AlertTitle>알림</AlertTitle>
          <AlertDescription>{msg}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Users className="h-5 w-5"/>사용자 정보</CardTitle>
          <CardDescription>팀/권한, 표시 이름 등 기본 정보를 수정합니다.</CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>아이디</Label>
            <Input value={form.id} onChange={e=>setForm(s=>({...s,id:e.target.value}))} />
          </div>
          <div className="space-y-2">
            <Label>팀</Label>
            <select className="border rounded-md px-3 py-2" value={form.team} onChange={e=>setForm(s=>({...s,team:e.target.value}))}>
              <option>R&D</option>
              <option>IP-Analyst</option>
              <option>Legal</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label>권한</Label>
            <select className="border rounded-md px-3 py-2" value={form.role} onChange={e=>setForm(s=>({...s,role:e.target.value}))}>
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <div className="md:col-span-3">
            <Button onClick={saveProfile}>프로필 저장</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>비밀번호 재설정 (관리자)</CardTitle>
          <CardDescription>사용자의 현재 비밀번호 없이 새 비밀번호를 설정합니다. (8자 이상)</CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>새 비밀번호</Label>
            <Input type="password" value={pw.next} onChange={e=>setPw(s=>({...s,next:e.target.value}))}/>
          </div>
          <div className="space-y-2">
            <Label>새 비밀번호 확인</Label>
            <Input type="password" value={pw.confirm} onChange={e=>setPw(s=>({...s,confirm:e.target.value}))}/>
          </div>
          <div className="md:col-span-3">
            <Button onClick={changePw}>비밀번호 재설정</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function LoginView({ onLogin }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-[70vh] grid place-items-center p-6">
      <Card className="w-full max-w-md shadow-xl border-muted-foreground/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><LogIn className="h-5 w-5"/>사내 로그인</CardTitle>
          <CardDescription>사번과 비밀번호로 로그인하세요. (IP 화이트리스트 적용)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="empId">아이디</Label>
            <Input id="empId" placeholder="e.g. sojung" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="pw">비밀번호</Label>
            <Input id="pw" type="password" placeholder="••••••••" />
          </div>
          <div className="flex items-center justify-between">
            <Button className="w-32" onClick={onLogin}>로그인</Button>
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button variant="link" className="px-0 text-muted-foreground">관리자에게 비밀번호 수정 요청</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>비밀번호 수정 요청</DialogTitle>
                  <DialogDescription>사유를 간단히 작성하면 관리자에게 알림이 전송됩니다.</DialogDescription>
                </DialogHeader>
                <div className="space-y-3">
                  <Label>사유</Label>
                  <Textarea rows={4} placeholder="분실/잠금 등" />
                </div>
                <DialogFooter>
                  <Button onClick={() => setOpen(false)}>요청 보내기</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function DualModeControls({ mode, setMode, resetWidths }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Button variant={mode==='split'?"default":"outline"} size="sm" onClick={()=>setMode('split')}>듀얼모드</Button>
        <Button variant={mode==='search'?"default":"outline"} size="sm" onClick={()=>setMode('search')}>검색만</Button>
        <Button variant={mode==='chat'?"default":"outline"} size="sm" onClick={()=>setMode('chat')}>챗봇만</Button>
      </div>
      <Button variant="ghost" size="sm" onClick={resetWidths}>레이아웃 초기화</Button>
    </div>
  );
}

function WorkspaceView() {
  const [historyOpen, setHistoryOpen] = useState(false);
  const [mode, setMode] = useState('split'); // 'split' | 'chat' | 'search'
  const [leftWidth, setLeftWidth] = useState(34); // 좌측 초기 폭(%)
  const usePrompt = (p) => { console.log('use prompt:', p); };

  // 드래그로 좌/우 폭 조절 (FIXED: avoid React pooled event by capturing element reference)
  const onDragHandle = (e) => {
    const handleEl = e.currentTarget; // capture element, not event
    const startX = e.clientX;
    const startLeft = leftWidth;

    const onMove = (ev) => {
      // Ensure container exists even if layout re-renders
      const container = safeGetSplitContainer(handleEl);
      if (!container) return; // early exit if DOM not ready

      const delta = ev.clientX - startX;
      const total = container.getBoundingClientRect().width;
      const next = computeNextLeftWidth(startLeft, delta, total);
      setLeftWidth(next);
    };

    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      document.body.style.cursor = '';
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    document.body.style.cursor = 'col-resize';
  };

  const resetWidths = () => setLeftWidth(34);

  return (
    <div className="p-4 md:p-6 space-y-4">
      <CannedPromptBar onUse={usePrompt}/>
      <DualModeControls mode={mode} setMode={setMode} resetWidths={resetWidths} />

      {/* 듀얼/단일 모드 컨테이너 */}
      {mode === 'split' && (
        <div className="flex gap-4 items-stretch">
          <div className="space-y-4" style={{ flexBasis: `${leftWidth}%` }}>
            <KeywordSearchPane />
          </div>
          {/* 드래그 핸들 */}
          <div
            onMouseDown={onDragHandle}
            className="w-1 cursor-col-resize bg-border rounded-full hover:bg-primary/40"
            aria-label="리사이즈 핸들"
            title="드래그로 폭 조절"
          />
          <div className="flex-1 min-w-0">
            <RightChatPane historyOpen={historyOpen} setHistoryOpen={setHistoryOpen} />
          </div>
        </div>
      )}

      {mode === 'search' && (
        <div className="grid"><div className="max-w-full"><KeywordSearchPane /></div></div>
      )}

      {mode === 'chat' && (
        <div className="grid"><div className="max-w-full"><RightChatPane historyOpen={historyOpen} setHistoryOpen={setHistoryOpen} /></div></div>
      )}

      {/* History drawer */}
      <Sheet open={historyOpen} onOpenChange={setHistoryOpen}>
        <SheetContent side="right" className="w-[420px] sm:w-[540px]">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2"><History className="h-5 w-5"/>대화 히스토리</SheetTitle>
            <SheetDescription>사용자 입력을 히스토리로 보관합니다.</SheetDescription>
          </SheetHeader>
          <div className="mt-4 space-y-3">
            {["UAV 균열탐지 신규성 확인", "배터리 파우치 팽창 측정 유사 특허", "의료기기 클래스 분류 기준 문의"].map((h, i) => (
              <div key={i} className="p-3 rounded-xl border hover:bg-muted/40 cursor-pointer">
                <div className="text-sm font-medium">{h}</div>
                <div className="text-xs text-muted-foreground">2025-10-03 14:{10+i}</div>
              </div>
            ))}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

// ---------------------------------------------
// Root component
// ---------------------------------------------
export default function VeraclaimMockup() {
  const [tab, setTab] = useState("login"); // "login" | "admin" | "workspace" | "profile"

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30 text-foreground">
      <Toolbar />
      <div className="mx-auto max-w-[1280px]">
        <div className="px-3 md:px-6 pt-4">
          <Tabs value={tab} onValueChange={(v)=>setTab(v)} className="w-full">
            <TabsList className="grid grid-cols-4 max-w-2xl">
              <TabsTrigger value="login">Login</TabsTrigger>
              <TabsTrigger value="admin">Admin</TabsTrigger>
              <TabsTrigger value="workspace">Workspace</TabsTrigger>
              <TabsTrigger value="profile">Profile</TabsTrigger>
            </TabsList>
            <TabsContent value="login"><LoginView onLogin={()=>setTab("workspace")} /></TabsContent>
            <TabsContent value="admin"><AdminView /></TabsContent>
            <TabsContent value="workspace"><WorkspaceView /></TabsContent>
            <TabsContent value="profile"><UserProfileView /></TabsContent>
          </Tabs>
        </div>
      </div>
      <footer className="text-xs text-muted-foreground p-6 text-center">© 2025 Veraclaim · 사내 전용 AI 허브 · IP 필터링 / 사내망 접속</footer>
    </div>
  );
}

// ---------------------------------------------
// Minimal dev self-tests (non-breaking) — existing + extra cases
// ---------------------------------------------
function runDevTests() {
  // Existing tests (do not change unless wrong)
  console.assert(Array.isArray(dummyTrends) && dummyTrends.length >= 5, "dummyTrends should have entries");
  console.assert(exampleHits.every(h => typeof h.id === 'string'), "exampleHits items should have id strings");
  const minPct = 20, maxPct = 70, initial = 34;
  console.assert(initial >= minPct && initial <= maxPct, "leftWidth default should be within bounds");

  // Added tests: computeNextLeftWidth boundaries
  console.assert(computeNextLeftWidth(34, 100, 0) === 34, "no container width should return start");
  const nextClampLow = computeNextLeftWidth(22, -1000, 500);
  console.assert(nextClampLow >= 20, "left width should not go below 20%");
  const nextClampHigh = computeNextLeftWidth(60, 1000, 500);
  console.assert(nextClampHigh <= 70, "left width should not exceed 70%");

  // Added tests: safeGetSplitContainer null-safety
  console.assert(safeGetSplitContainer(null) === null, "safeGetSplitContainer should handle null");

  // Added tests: password validation
  console.assert(validatePasswordChange("abc", "abcdefg", "abcdefg").ok === false, "should fail when new < 8 chars");
  console.assert(validatePasswordChange("current1", "current1", "current1").ok === false, "should fail when new equals current");
  console.assert(validatePasswordChange("current1", "newpassword", "mismatch").ok === false, "should fail when confirm mismatches");
  console.assert(validatePasswordChange("current1", "newpassword", "newpassword").ok === true, "should pass with valid inputs");

  // Added tests: admin password set without current
  console.assert(validatePasswordSetAdmin("short", "short").ok === false, "admin set should fail when new < 8 chars");
  console.assert(validatePasswordSetAdmin("newpassword", "mismatch").ok === false, "admin set should fail on mismatch");
  console.assert(validatePasswordSetAdmin("newpassword", "newpassword").ok === true, "admin set should pass with valid inputs");

  // Added tests: buildUserRecord purity
  const rec = buildUserRecord("alice", "R&D", "admin");
  console.assert(rec.id === "alice" && rec.team === "R&D" && rec.role === "admin" && typeof rec.lastActive === 'string', "buildUserRecord should return normalized shape");
}

// Execute tests in dev only
if (typeof process !== 'undefined' && process.env && process.env.NODE_ENV !== 'production') {
  try { runDevTests(); } catch (e) { console.warn('Dev tests failed:', e); }
}