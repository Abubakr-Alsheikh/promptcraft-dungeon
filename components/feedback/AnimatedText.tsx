import { useState, useEffect } from "react";
import { Text, TextProps, chakra, shouldForwardProp } from "@chakra-ui/react";
import { isValidMotionProp, motion } from "framer-motion";

const MotionText = chakra(motion(Text), {
  shouldForwardProp: (prop) =>
    isValidMotionProp(prop) || shouldForwardProp(prop),
});

interface AnimatedTextProps extends TextProps {
  text: string;
  speed?: number; // Characters per second
  onComplete?: () => void; // Callback when animation finishes
}

export function AnimatedText({
  text,
  speed = 60,
  onComplete,
  ...rest
}: AnimatedTextProps) {
  const [displayedText, setDisplayedText] = useState("");
  const delay = 1000 / speed; // milliseconds per character

  useEffect(() => {
    setDisplayedText(""); // Reset when text changes
    let i = 0;
    const intervalId = setInterval(() => {
      setDisplayedText((prev) => prev + text.charAt(i));
      i++;
      if (i >= text.length) {
        clearInterval(intervalId);
        if (onComplete) {
          onComplete();
        }
      }
    }, delay);

    return () => clearInterval(intervalId); // Cleanup on unmount or text change
  }, [text, delay, onComplete]);

  // Using opacity animation for smoother appearance, combine with interval update
  return (
    <MotionText
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      whiteSpace="pre-wrap" // Preserve line breaks from the LLM
      {...rest}
    >
      {displayedText}
      {/* Blinking cursor simulation */}
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: [0, 1, 0] }}
        transition={{ duration: 0.8, repeat: Infinity }}
        style={{
          display: displayedText.length === text.length ? "none" : "inline",
          marginLeft: "2px",
          borderLeft: "2px solid", // Use theme color if possible
          position: "relative",
          top: "0.1em",
        }}
      >
          {/* Non-breaking space to give cursor width */}
      </motion.span>
    </MotionText>
  );
}

// Note: For long texts, this interval approach can be slightly inefficient.
// Libraries like 'react-type-animation' might offer more robust solutions if needed.
