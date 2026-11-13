import { Suspense } from "react";
import RegistrationForm from "./RegistrationForm";

export default function RegistrationPage() {
  return (
    <Suspense fallback={null}>
      <RegistrationForm />
    </Suspense>
  );
}
