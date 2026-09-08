import Header from "@/components/landing/Header";
import HeroSection from "@/components/landing/HeroSection";
import StatsSection from "@/components/landing/StatsSection";
import FeaturesSection from "@/components/landing/FeaturesSection";
import ComoFunciona from "@/components/landing/ComoFunciona";
import DashboardPreview from "@/components/landing/DashboardPreview";
import ChatbotSection from "@/components/landing/ChatbotSection";
import RolesSection from "@/components/landing/RolesSection";
import Testimonios from "@/components/landing/Testimonios";
import Pricing from "@/components/landing/Pricing";
import FAQ from "@/components/landing/FAQ";
import CTASection from "@/components/landing/CTASection";
import Footer from "@/components/landing/Footer";

// Landing pública: presentación del producto antes de login/registro.
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-surface scroll-smooth overflow-x-clip">
      <Header />
      <main>
        <HeroSection />
        <StatsSection />
        <FeaturesSection />
        <ComoFunciona />
        <DashboardPreview />
        <ChatbotSection />
        <RolesSection />
        <Testimonios />
        <Pricing />
        <FAQ />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
