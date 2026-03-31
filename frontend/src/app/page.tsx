import ChatBox from "@/components/ChatBox";

export default function Home() {
  return (
    <main className="min-h-screen gradient-bg flex flex-col items-center justify-center p-4 md:p-8">
      {/* Decorative background elements */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#ed1c24]/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-[#ffcb05]/5 blur-[120px] rounded-full pointer-events-none" />
      
      <div className="w-full h-[85vh] max-h-[900px] flex items-center justify-center">
        <ChatBox />
      </div>
      
      <div className="mt-8 text-white/30 text-sm font-medium tracking-tight uppercase">
        BANCO DE BOGOTÁ • Mi Llave • 2026
      </div>
    </main>
  );
}
