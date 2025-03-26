"use client";

import { Heading, Text, Button, VStack, Container } from "@chakra-ui/react";
import NextLink from "next/link";

export default function HomePage() {
  return (
    <Container centerContent maxW="container.md" py={20}>
      <VStack spacing={6} textAlign="center">
        <Heading as="h1" size="2xl" fontFamily="heading" color="brand.accent">
          PromptCraft: Dungeon Delver
        </Heading>
        <Text fontSize="xl" color="brand.textLight">
          An AI-powered text adventure awaits. Delve into dungeons crafted by
          language itself!
        </Text>
        <Button
          as={NextLink}
          href="/game"
          colorScheme="yellow"
          variant="solid"
          size="lg"
          bg="brand.accent"
          color="brand.bgDark"
          _hover={{ bg: "yellow.400" }}
        >
          Begin Your Adventure!
        </Button>
      </VStack>
    </Container>
  );
}
