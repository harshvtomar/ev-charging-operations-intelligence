let
    Source = Csv.Document(File.Contents(FolderPath & "FactMonthly.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"month", type text}, {"segment", type text}, {"sessions", type number}, {"successes", type number}, {"energy_kwh", type number}, {"revenue", type number}, {"contribution", type number}, {"planned_hours", Int64.Type}, {"available_hours", type number}, {"occupied_hours", type number}, {"month_date", type date}}, "en-US")
in
    Typed
