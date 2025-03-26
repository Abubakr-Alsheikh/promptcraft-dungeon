import {
  Progress,
  Text,
  VStack,
  ProgressLabel,
  useTheme,
  ThemingProps,
} from "@chakra-ui/react";

interface ProgressBarProps {
  value: number;
  max: number;
  label?: string;
  colorScheme?: ThemingProps<"Progress">["colorScheme"]; // Allow specific color schemes
  showValue?: boolean; // Option to show "current / max" text
}

export function ProgressBar({
  value,
  max,
  label,
  colorScheme = "yellow", // Default to accent color
  showValue = true,
}: ProgressBarProps) {
  const theme = useTheme();
  const percentage = max > 0 ? (value / max) * 100 : 0;

  // Determine color based on value (example for HP)
  let dynamicColorScheme = colorScheme;
  if (
    label?.toLowerCase().includes("health") ||
    label?.toLowerCase().includes("hp")
  ) {
    if (percentage < 25) dynamicColorScheme = "red";
    else if (percentage < 60) dynamicColorScheme = "orange";
    else dynamicColorScheme = "green"; // Or keep the passed 'colorScheme'
  }

  return (
    <VStack align="stretch" spacing={1} w="full">
      {label && (
        <Text
          fontSize="sm"
          fontWeight="bold"
          color="brand.textLight"
          casing="uppercase"
        >
          {label}
        </Text>
      )}
      <Progress
        value={percentage}
        size="sm"
        colorScheme={dynamicColorScheme}
        bgColor="gray.600" // Darker background for contrast
        borderRadius="md"
        hasStripe
        isAnimated={percentage < 100} // Animate only while not full
      >
        {showValue && (
          <ProgressLabel
            fontSize="xs"
            color={percentage > 50 ? "gray.800" : "white"} // Adjust text color for visibility
            fontWeight="bold"
            px={2} // Add padding inside the label
          >{`${value} / ${max}`}</ProgressLabel>
        )}
      </Progress>
    </VStack>
  );
}
