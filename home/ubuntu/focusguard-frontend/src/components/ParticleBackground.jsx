import React, { useEffect, useState } from 'react';

const ParticleBackground = () => {
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    const createParticle = () => {
      return {
        id: Math.random(),
        left: Math.random() * 100,
        animationDelay: Math.random() * 20,
        animationDuration: 15 + Math.random() * 10,
      };
    };

    // Create initial particles
    const initialParticles = Array.from({ length: 50 }, createParticle);
    setParticles(initialParticles);

    // Add new particles periodically
    const interval = setInterval(() => {
      setParticles(prev => {
        const newParticles = [...prev];
        if (newParticles.length < 80) {
          newParticles.push(createParticle());
        }
        return newParticles;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="particles">
      {particles.map(particle => (
        <div
          key={particle.id}
          className="particle"
          style={{
            left: `${particle.left}%`,
            animationDelay: `${particle.animationDelay}s`,
            animationDuration: `${particle.animationDuration}s`,
          }}
        >
          •
        </div>
      ))}
    </div>
  );
};

export default ParticleBackground;

