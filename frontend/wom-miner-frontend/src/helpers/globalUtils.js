export default {
    formatDateTime: function (dateTime) {
        const date = new Date(dateTime);
        let day = date.getDate();
        let month = date.getMonth() + 1; // Months are zero-indexed
        const year = date.getFullYear();
        const hours = date.getHours();
        const minutes = date.getMinutes();

        if(day < 10)
            day = '0'+ day
        if(month < 10)
            month = '0'+ month

        const formattedDate = `${day}/${month}/${year}`;
        const formattedTime = `${hours}:${minutes.toString().padStart(2, '0')}`;

        return `${formattedDate} at ${formattedTime}`;
    },
    extractUniFromIndex: function (index) {
        if (index.toLowerCase().includes("-rub"))
            return "RUB"
        else
            return "UDE"
    },
    wrapTextInTable: function (text) {
        if (text.length > 95)
            text = text.substring(0, 95) + "...";
        return text
    },
    extractTypeFromIndex: function (index){
        if(index.includes("research_project"))
            return "research project"
        else if (index.includes("people"))
            return "people"
        return "organization"
    },
    extractTypeFromDocument: function (index){
        if(index.includes("research_project"))
            return "R"
        else if (index.includes("people"))
            return "P"
        else if (index.includes("institute"))
            return "I"
        else if (index.includes("chair"))
            return "C"
        else if (index.includes("Faculty"))
            return "F"
        return "N"
    },
    sortByLastUpdate: function (items){
        items.sort(function (a, b){
            return b.sort[0].localeCompare(a.sort[0])
        })
        return items
    },
    extractPersons: function (items){
        return items.reduce((unique, item) => {
            return unique.includes(item) ? unique : [...unique, item];
        }, [])
    },
    capitalize: function (string) {
        if(string === undefined)
            return
        string = string.toLowerCase()
        return string.charAt(0).toUpperCase() + string.slice(1);
    },
    extractTopXByType(dataList, targetType, x){
        const filteredData = dataList.filter((item) => this.extractTypeFromIndex(item._index) === targetType);
        filteredData.sort((a, b) => b.score - a.score);

        if(x !== -1)
            return filteredData.slice(0, x);
        else
            return filteredData
    }

}