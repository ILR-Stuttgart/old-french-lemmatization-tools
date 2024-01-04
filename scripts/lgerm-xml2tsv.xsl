<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"
    version="1.0">
    
    <xsl:output method="text" encoding="UTF-8"/>
        
    <xsl:template match="formSet">
        <xsl:apply-templates select="lemmatizedForm"/>
        <xsl:text>&#x0009;</xsl:text> <!-- Tab -->
        <!-- Print first inflectedForm -->
        <xsl:value-of select="inflectedForm[1]/orthography[1]/text()"/>
        <!-- Apply template to the rest -->
        <xsl:apply-templates select="inflectedForm[position() &gt; 1]"/>
        <xsl:text>&#x000A;</xsl:text> <!-- newline -->
    </xsl:template>
    
    <xsl:template match="lemmatizedForm">
        <!-- Take the first orthography node -->
        <xsl:value-of select="orthography[position()=1]/text()"/>
        <xsl:text>&#x0009;</xsl:text> <!-- Tab -->
        <!-- Print the pos tag -->
        <xsl:value-of select="grammaticalCategory[position()=1]/text()"/>
    </xsl:template>
    
    <xsl:template match="inflectedForm">
        <xsl:text>|</xsl:text>
        <xsl:value-of select="orthography[1]/text()"/>
    </xsl:template>
    
    <xsl:template match="*">
        <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="text()">
        <!-- don't repeat text by default -->
        <xsl:apply-templates/>
    </xsl:template>
    
</xsl:stylesheet>


