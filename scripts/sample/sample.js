const header = require('./header');

function get_column(jsonData){
    const {header, data} = jsonData;
  
    const IMAGE = /^Profile_Image$/;
    const SEM = /.+Sem_(\d+)$/;
  
    var profile_col = []
    var sem_col = []
    var personal_col = []
  
    Object.keys(data).forEach((col) => {
        if(IMAGE.test(col)){
          profile_col.push(col);
        }
        else if(SEM.test(col)){
          sem_col.push(col);
        }
        else{
          personal_col.push(col);
        }
    }); 
  
    var sem_dict = Object({});
    profile_col = profile_col[0];
  
    sem_col.forEach((col) =>{
  
      const sem = SEM.exec(col);
  
      if(!sem_dict.hasOwnProperty(sem[1])){
        sem_dict[sem[1]] = [];
      }
  
      sem_dict[sem[1]].push(col);
  
    });
  
    return {profile_col,sem_dict,personal_col,header}
  }

// console.log(get_column(header));
