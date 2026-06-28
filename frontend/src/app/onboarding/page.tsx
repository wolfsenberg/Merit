"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileCheck, Zap, Shield, Banknote, ArrowRight, ChevronRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
  highlight: string;
}

const features: Feature[] = [
  {
    icon: Zap,
    title: "No more long queues",
    description: "Your scholarship organization handles verification. You just accept the funds directly in the app — no windows, no waiting.",
    highlight: "Apply from anywhere, anytime.",
  },
  {
    icon: FileCheck,
    title: "Receive funds instantly",
    description: "Once verified by your scholarship provider, funds land in your Merit wallet immediately. Like GCash, but for scholars.",
    highlight: "No more delayed stipends.",
  },
  {
    icon: Shield,
    title: "Built-in savings goals",
    description: "Set goals like 'Laptop Fund' or 'Emergency'. Lock your money until you hit the target — discipline made easy.",
    highlight: "Your money works for you.",
  },
  {
    icon: Banknote,
    title: "Cash out anytime",
    description: "Transfer to GCash, bank account, or keep it in your Merit wallet. Powered by blockchain, but feels like any other app.",
    highlight: "No crypto knowledge needed.",
  },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [currentSlide, setCurrentSlide] = useState(0);

  const handleNext = () => {
    if (currentSlide < features.length - 1) {
      setCurrentSlide(currentSlide + 1);
    } else {
      handleFinish();
    }
  };

  const handleSkip = () => {
    handleFinish();
  };

  const handleFinish = () => {
    localStorage.setItem("merit_onboarding_seen", "true");
    router.push("/login");
  };

  const current = features[currentSlide];
  const Icon = current.icon;
  const isLast = currentSlide === features.length - 1;

  return (
    <div className="flex min-h-screen flex-col bg-[#FAFAF9]">
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-5 md:px-8 md:pt-8">
        <div className="flex items-center gap-2">
          <img src="/logo.svg" alt="Merit" className="h-7 w-7" />
          <span className="text-[15px] font-semibold text-gray-900">Merit</span>
        </div>
        <button
          onClick={handleSkip}
          className="text-[12px] font-medium text-gray-400 hover:text-gray-600 transition-colors"
        >
          Skip
        </button>
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12 md:px-8">
        <div className="w-full max-w-[380px] text-center">
          {/* Icon */}
          <div className="mx-auto mb-8 flex h-16 w-16 items-center justify-center rounded-2xl bg-merit-gold/10 border border-merit-gold/20">
            <Icon className="h-7 w-7 text-merit-gold" strokeWidth={1.5} />
          </div>

          {/* Title */}
          <h1 className="text-[24px] font-semibold tracking-tight text-gray-900 leading-tight">
            {current.title}
          </h1>

          {/* Description */}
          <p className="mt-4 text-[14px] leading-relaxed text-gray-500">
            {current.description}
          </p>

          {/* Highlight */}
          <p className="mt-3 text-[13px] font-medium text-merit-gold">
            {current.highlight}
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 pb-8 md:px-8 md:pb-10">
        <div className="mx-auto w-full max-w-[380px]">
          {/* Dots */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {features.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentSlide(idx)}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  idx === currentSlide ? "w-6 bg-merit-gold" : "w-1.5 bg-gray-200"
                }`}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>

          {/* Button */}
          <button
            onClick={handleNext}
            className="w-full flex items-center justify-center gap-2 h-11 rounded-xl bg-gray-900 hover:bg-gray-800 text-white text-[14px] font-medium transition-all"
          >
            {isLast ? (
              <>
                Get Started
                <ArrowRight className="h-4 w-4" strokeWidth={2} />
              </>
            ) : (
              <>
                Continue
                <ChevronRight className="h-4 w-4" strokeWidth={2} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
