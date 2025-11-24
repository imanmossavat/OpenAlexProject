import { Check } from 'lucide-react'

export default function Stepper({ currentStep, steps }) {
  return (
    <div className="w-full max-w-2xl mx-auto mb-12">
      <div className="flex items-start justify-between">
        {steps.map((step, index) => {
          const stepNumber = index + 1
          const isActive = stepNumber === currentStep
          const isCompleted = stepNumber < currentStep
          const isNextStep = stepNumber === currentStep + 1
          
          return (
            <div key={step} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center relative">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm z-10 ${
                    isActive || isCompleted
                      ? 'bg-purple-600 text-white'
                      : 'border-2 border-gray-300 bg-white text-gray-400'
                  }`}
                >
                  {isCompleted ? <Check className="w-4 h-4" /> : stepNumber}
                </div>
                <span
                  className={`mt-2 text-xs whitespace-nowrap ${
                    isActive ? 'font-semibold text-black' : 'text-gray-500'
                  }`}
                >
                  {step}
                </span>
              </div>
              
              {index < steps.length - 1 && (
                <div 
                  className={`flex-1 h-[2px] -mx-0 self-start mt-4 ${
                    isCompleted || isActive ? 'bg-purple-600' : 'bg-gray-300'
                  }`}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}