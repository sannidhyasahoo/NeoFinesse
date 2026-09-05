import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import crypto from "crypto";
import JSZip from "jszip";

// Helper: Convert column letter to 1-indexed number (e.g. 'A' -> 1, 'F' -> 6, 'AA' -> 27)
function columnLetterToIndex(colLetter: string): number {
  const clean = colLetter.trim().toUpperCase();
  let result = 0;
  for (let i = 0; i < clean.length; i++) {
    const code = clean.charCodeAt(i);
    if (code >= 65 && code <= 90) {
      result = result * 26 + (code - 65 + 1);
    } else {
      throw new Error(`Invalid column character: ${clean[i]}`);
    }
  }
  return result;
}

// Helper: Convert 1-indexed number to column letter (e.g. 1 -> 'A', 6 -> 'F', 27 -> 'AA')
function indexToColumnLetter(index: number): string {
  if (index < 1) throw new Error("Index must be >= 1");
  let col = "";
  let idx = index;
  while (idx > 0) {
    const rem = (idx - 1) % 26;
    col = String.fromCharCode(65 + rem) + col;
    idx = Math.floor((idx - 1) / 26);
  }
  return col;
}

// Helper: Parse cell reference string (e.g., "H42", "Settlements!H42", "'Account Statement'!C19")
function parseCellReference(cellRef: string): { sheet: string | null; colLetter: string; colIdx: number; rowIdx: number } {
  const trimmed = cellRef.trim();
  let sheet: string | null = null;
  let addr = trimmed;

  if (trimmed.includes("!")) {
    const parts = trimmed.split("!");
    sheet = parts[0].replace(/^['"]|['"]$/g, "").trim();
    addr = parts[1].trim();
  }

  const match = addr.match(/^([A-Za-z]+)(\d+)$/);
  if (!match) {
    throw new Error(`Invalid cell format: ${cellRef}`);
  }

  const colLetter = match[1].toUpperCase();
  const rowIdx = parseInt(match[2], 10);
  const colIdx = columnLetterToIndex(colLetter);

  return { sheet, colLetter, colIdx, rowIdx };
}

// Parse CSV lines handling quoted fields correctly
function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"' || char === "'") {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      result.push(cur.trim());
      cur = "";
    } else {
      cur += char;
    }
  }
  result.push(cur.trim());
  return result;
}

// Format string cell value into numeric or clean representation
function formatCellValue(val: any): any {
  if (val === null || val === undefined || val === "") return "";
  const s = String(val).trim();
  if (/^-?\d+$/.test(s)) {
    const num = parseInt(s, 10);
    return isNaN(num) ? s : num;
  }
  if (/^-?\d+\.\d+$/.test(s)) {
    const flt = parseFloat(s);
    return isNaN(flt) ? s : flt;
  }
  return s;
}

// Parse XLSX workbook directly via JSZip without external binaries
async function parseXlsxWorkbook(fileBuffer: Buffer, targetSheetName?: string | null): Promise<{ sheetNames: string[]; activeSheet: string; rows: string[][] }> {
  const zip = await JSZip.loadAsync(fileBuffer);
  const sheetNames: string[] = [];
  const sheetMap: Record<string, string> = {};

  // Read workbook.xml to get sheet names
  const workbookXmlFile = zip.file("xl/workbook.xml");
  if (workbookXmlFile) {
    const wbXml = await workbookXmlFile.async("string");
    const sheetMatches = wbXml.matchAll(/<sheet[^>]+name="([^"]+)"[^>]+r:id="([^"]+)"/g);
    for (const match of sheetMatches) {
      const name = match[1];
      const rId = match[2];
      sheetNames.push(name);
      sheetMap[name] = rId;
    }
  }

  // Read rels to map r:id to target sheet XML path
  const relsXmlFile = zip.file("xl/_rels/workbook.xml.rels");
  const idToPath: Record<string, string> = {};
  if (relsXmlFile) {
    const relsXml = await relsXmlFile.async("string");
    const relMatches = relsXml.matchAll(/<Relationship[^>]+Id="([^"]+)"[^>]+Target="([^"]+)"/g);
    for (const match of relMatches) {
      idToPath[match[1]] = match[2].replace(/^\//, "");
    }
  }

  // Read shared strings
  const sharedStrings: string[] = [];
  const ssFile = zip.file("xl/sharedStrings.xml");
  if (ssFile) {
    const ssXml = await ssFile.async("string");
    const siMatches = ssXml.matchAll(/<si>(.*?)<\/si>/gs);
    for (const si of siMatches) {
      const textMatches = Array.from(si[1].matchAll(/<t[^>]*>(.*?)<\/t>/gs));
      const fullText = textMatches.map((m) => m[1]).join("");
      sharedStrings.push(fullText);
    }
  }

  // Pick active sheet
  let activeSheet = targetSheetName || (sheetNames.length > 0 ? sheetNames[0] : "Sheet1");
  if (!sheetNames.includes(activeSheet)) {
    const matched = sheetNames.find((s) => s.toLowerCase() === activeSheet.toLowerCase());
    if (matched) activeSheet = matched;
    else if (sheetNames.length > 0) activeSheet = sheetNames[0];
  }

  const rId = sheetMap[activeSheet];
  let sheetRelPath = rId && idToPath[rId] ? `xl/${idToPath[rId]}` : "xl/worksheets/sheet1.xml";
  let sheetFile = zip.file(sheetRelPath) || zip.file("xl/worksheets/sheet1.xml");

  const rows: string[][] = [];
  if (sheetFile) {
    const sheetXml = await sheetFile.async("string");
    const rowMatches = sheetXml.matchAll(/<row[^>]+r="(\d+)"[^>]*>(.*?)<\/row>/gs);
    for (const rMatch of rowMatches) {
      const rowIdx = parseInt(rMatch[1], 10);
      const rowContent = rMatch[2];
      const cellMatches = rowContent.matchAll(/<c[^>]+r="([A-Za-z]+)(\d+)"(?:[^>]+t="([^"]+)")?[^>]*>(?:<v>(.*?)<\/v>)?<\/c>/gs);

      while (rows.length < rowIdx) {
        rows.push([]);
      }
      const currentRow = rows[rowIdx - 1];

      for (const cMatch of cellMatches) {
        const colLetter = cMatch[1];
        const colIdx = columnLetterToIndex(colLetter);
        const cellType = cMatch[3];
        const rawVal = cMatch[4] || "";

        let parsedVal = rawVal;
        if (cellType === "s") {
          const sIdx = parseInt(rawVal, 10);
          parsedVal = sIdx < sharedStrings.length ? sharedStrings[sIdx] : rawVal;
        }

        while (currentRow.length < colIdx) {
          currentRow.push("");
        }
        currentRow[colIdx - 1] = parsedVal;
      }
    }
  }

  return { sheetNames, activeSheet, rows };
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const filename = searchParams.get("file") || searchParams.get("filename");
    const sheetParam = searchParams.get("sheet");
    const cellParam = searchParams.get("cell");
    const rowParam = searchParams.get("row");
    const colParam = searchParams.get("column") || searchParams.get("col");
    const rowRadius = parseInt(searchParams.get("row_radius") || "3", 10);
    const colRadius = parseInt(searchParams.get("column_radius") || "3", 10);

    if (!filename) {
      return NextResponse.json({ status: "ERROR", error: "Missing required parameter 'file'" }, { status: 400 });
    }

    // Security check: Prevent directory traversal
    const baseName = path.basename(filename);
    if (baseName !== filename.trim() || filename.includes("..") || filename.includes("/") || filename.includes("\\")) {
      return NextResponse.json({ status: "ERROR", error: "Directory traversal prohibited" }, { status: 403 });
    }

    // Resolve file from known data directories
    const candidateDirs = [
      path.resolve(process.cwd(), "..", "data", "demo_dataset"),
      path.resolve(process.cwd(), "data", "demo_dataset"),
      path.resolve(process.cwd(), "..", "data"),
      path.resolve(process.cwd(), "data"),
      path.resolve(process.cwd(), "public", "data"),
      path.resolve(process.cwd(), "..", "src", "neofinesse", "ui", "data"),
    ];

    let resolvedPath: string | null = null;
    for (const dir of candidateDirs) {
      const checkPath = path.join(dir, baseName);
      if (fs.existsSync(checkPath) && fs.statSync(checkPath).isFile()) {
        resolvedPath = checkPath;
        break;
      }
    }

    if (!resolvedPath) {
      return NextResponse.json(
        {
          status: "UNAVAILABLE",
          error: `Source file '${baseName}' is not registered in source dataset.`,
          source_file: baseName,
          is_provenance_verified: false,
        },
        { status: 404 }
      );
    }

    // Parse target row and column
    let targetSheet = sheetParam;
    let targetRow = rowParam ? parseInt(rowParam, 10) : null;
    let targetColIdx: number | null = null;
    let targetColLetter: string | null = null;

    if (cellParam) {
      const parsed = parseCellReference(cellParam);
      if (parsed.sheet && !targetSheet) targetSheet = parsed.sheet;
      targetRow = parsed.rowIdx;
      targetColIdx = parsed.colIdx;
      targetColLetter = parsed.colLetter;
    } else if (colParam) {
      if (/^\d+$/.test(colParam)) {
        targetColIdx = parseInt(colParam, 10);
        targetColLetter = indexToColumnLetter(targetColIdx);
      } else {
        targetColLetter = colParam.toUpperCase();
        targetColIdx = columnLetterToIndex(targetColLetter);
      }
    }

    if (!targetRow || !targetColIdx) {
      return NextResponse.json(
        { status: "ERROR", error: "Target cell coordinates must be provided via 'cell' or ('row', 'column')." },
        { status: 400 }
      );
    }

    // Compute cryptographic file SHA-256 hash
    const fileBuffer = fs.readFileSync(resolvedPath);
    const fileHash = crypto.createHash("sha256").update(fileBuffer).digest("hex");

    let allRows: string[][] = [];
    let activeSheet = targetSheet || "Sheet1";

    const isXlsx = baseName.toLowerCase().endsWith(".xlsx") || baseName.toLowerCase().endsWith(".xls");
    if (isXlsx) {
      const parsedXlsx = await parseXlsxWorkbook(fileBuffer, targetSheet);
      allRows = parsedXlsx.rows;
      activeSheet = parsedXlsx.activeSheet;
    } else {
      const content = fs.readFileSync(resolvedPath, "utf-8");
      allRows = content
        .split(/\r?\n/)
        .filter((l) => l.trim().length > 0)
        .map(parseCsvLine);
    }

    const totalRows = allRows.length;
    const totalCols = allRows.length > 0 ? Math.max(...allRows.map((r) => r.length)) : 0;

    targetColLetter = targetColLetter || indexToColumnLetter(targetColIdx);
    const targetCellAddr = `${targetColLetter}${targetRow}`;

    // Validate bounds
    if (targetRow > totalRows || targetColIdx > totalCols) {
      return NextResponse.json(
        {
          status: "UNAVAILABLE",
          error: `Source record unavailable: requested coordinate ${targetCellAddr} exceeds source file boundaries (total rows: ${totalRows}, total columns: ${totalCols}).`,
          source_file: baseName,
          sheet: activeSheet,
          target_cell: targetCellAddr,
          target_row: targetRow,
          target_column: targetColIdx,
          target_column_letter: targetColLetter,
          file_hash: fileHash,
          is_provenance_verified: false,
          total_rows: totalRows,
          total_columns: totalCols,
        },
        { status: 200 }
      );
    }

    const minRow = Math.max(1, targetRow - rowRadius);
    const maxRow = Math.min(totalRows, targetRow + rowRadius);
    const minCol = Math.max(1, targetColIdx - colRadius);
    const maxCol = Math.min(totalCols, targetColIdx + colRadius);

    const headers = allRows.length > 0 ? allRows[0] : [];

    let targetValue: any = null;
    let targetRowContent: string[] = [];

    if (targetRow >= 1 && targetRow <= totalRows) {
      targetRowContent = allRows[targetRow - 1] || [];
      if (targetColIdx >= 1 && targetColIdx <= targetRowContent.length) {
        targetValue = formatCellValue(targetRowContent[targetColIdx - 1]);
      }
    }

    const recordHash = crypto
      .createHash("sha256")
      .update(targetRowContent.join(","))
      .digest("hex");

    const columnsMeta = [];
    for (let c = minCol; c <= maxCol; c++) {
      const cLetter = indexToColumnLetter(c);
      const headerName = c - 1 < headers.length && headers[c - 1] ? headers[c - 1] : `Column ${cLetter}`;
      columnsMeta.push({
        index: c,
        letter: cLetter,
        header: headerName,
        is_target_column: c === targetColIdx,
      });
    }

    const rowsData = [];
    for (let r = minRow; r <= maxRow; r++) {
      const rowRaw = r - 1 < allRows.length ? allRows[r - 1] : [];
      const cells = [];
      for (let c = minCol; c <= maxCol; c++) {
        const cLetter = indexToColumnLetter(c);
        const rawVal = c - 1 < rowRaw.length ? rowRaw[c - 1] : "";
        const formattedVal = formatCellValue(rawVal);

        cells.push({
          address: `${cLetter}${r}`,
          row: r,
          column: c,
          column_letter: cLetter,
          value: formattedVal,
          raw_value: rawVal,
          is_target: r === targetRow && c === targetColIdx,
        });
      }

      rowsData.push({
        row_number: r,
        is_target_row: r === targetRow,
        cells,
      });
    }

    return NextResponse.json({
      status: "SUCCESS",
      source_file: baseName,
      sheet: activeSheet,
      target_cell: targetCellAddr,
      target_row: targetRow,
      target_column: targetColIdx,
      target_column_letter: targetColLetter,
      target_value: targetValue,
      file_hash: fileHash,
      record_hash: recordHash,
      is_provenance_verified: true,
      total_rows: totalRows,
      total_columns: totalCols,
      window: {
        min_row: minRow,
        max_row: maxRow,
        min_col: minCol,
        max_col: maxCol,
        row_radius: rowRadius,
        column_radius: colRadius,
      },
      context: {
        columns: columnsMeta,
        rows: rowsData,
      },
    });
  } catch (err: any) {
    return NextResponse.json({ status: "ERROR", error: err.message || "Failed to load cell context" }, { status: 500 });
  }
}
