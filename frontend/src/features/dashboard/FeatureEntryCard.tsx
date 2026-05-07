import type { LucideIcon } from "lucide-react";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

interface FeatureEntryCardProps {
  title: string;
  description: string;
  to: string;
  icon: LucideIcon;
  active?: boolean;
}

export function FeatureEntryCard({ title, description, to, icon: Icon, active = false }: FeatureEntryCardProps) {
  return (
    <Link className={active ? "feature-card is-active" : "feature-card"} to={to}>
      <div className="feature-card__icon">
        <Icon size={20} />
      </div>
      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <ArrowRight className="feature-card__arrow" size={18} />
    </Link>
  );
}
